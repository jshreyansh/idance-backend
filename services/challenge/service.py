from fastapi import APIRouter, HTTPException, Depends
from services.challenge.models import (
    Challenge, ChallengeCreate, ChallengeResponse, ChallengeListResponse, 
    TodayChallengeResponse, ChallengeCriteria, ChallengeSearchRequest,
    ChallengeLeaderboardResponse, ChallengeLeaderboardEntry, PublicChallengeSubmissionsResponse, PublicSubmissionEntry
)
from services.user.service import get_current_user_id
from infra.mongo import Database
# Environment-aware collection names
challenges_collection = Database.get_collection_name('challenges')
challenge_submissions_collection = Database.get_collection_name('challenge_submissions')
users_collection = Database.get_collection_name('users')

from datetime import datetime, timedelta
from bson import ObjectId
from typing import List, Optional
from services.video_processing.background_service import background_video_processor
import os
import logging

logger = logging.getLogger(__name__)

challenge_router = APIRouter()

class ChallengeService:
    def __init__(self):
        self.db = None
    
    def _get_db(self):
        if self.db is None:
            self.db = Database.get_database()
        return self.db
    
    async def create_challenge(self, challenge_data: ChallengeCreate, user_id: str) -> str:
        """Create a new challenge (admin only)"""
        # Validate date range
        if challenge_data.startTime >= challenge_data.endTime:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        # Set default scoring criteria if not provided
        if not challenge_data.scoringCriteria:
            challenge_data.scoringCriteria = ChallengeCriteria()
        
        # Handle demo video URL/file key
        demo_video_url = None
        demo_video_file_key = None
        
        if challenge_data.demoVideoURL:
            # Use direct URL
            demo_video_url = challenge_data.demoVideoURL
            demo_video_file_key = f"challenges/demo/external_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
        elif challenge_data.demoVideoFileKey:
            # Use S3 file key and generate URL
            demo_video_file_key = challenge_data.demoVideoFileKey
            demo_video_url = self._generate_video_url(challenge_data.demoVideoFileKey)
        else:
            raise HTTPException(status_code=400, detail="Either demoVideoURL or demoVideoFileKey must be provided")
        
        now = datetime.utcnow()
        challenge_doc = {
            "title": challenge_data.title,
            "description": challenge_data.description,
            "type": challenge_data.type,
            "difficulty": challenge_data.difficulty,
            "startTime": challenge_data.startTime,
            "endTime": challenge_data.endTime,
            "demoVideoURL": demo_video_url,
            "demoVideoFileKey": demo_video_file_key,
            "thumbnailURL": challenge_data.thumbnailURL,
            "points": challenge_data.points,
            "badgeName": challenge_data.badgeName,
            "badgeIconURL": challenge_data.badgeIconURL,
            "scoringCriteria": challenge_data.scoringCriteria.dict(),
            "categories": challenge_data.categories or [],
            "tags": challenge_data.tags or [],
            "isActive": True,
            "createdBy": user_id,
            "createdAt": now,
            "updatedAt": now,
            "totalSubmissions": 0,
            "averageScore": 0.0,
            "topScore": 0,
            "participantCount": 0
        }
        
        result = await self._get_db()[challenges_collection].insert_one(challenge_doc)
        challenge_id = str(result.inserted_id)
        
        # Queue background video processing for demo video mobile compatibility (NEW)
        if demo_video_url:
            try:
                await background_video_processor.queue_demo_video_processing(
                    challenge_id=challenge_id,
                    video_url=demo_video_url,
                    user_id=user_id
                )
                logger.info(f"🎯 Queued background video processing for demo video: {challenge_id}")
                logger.info(f"📹 Processing URL: {demo_video_url}")
            except Exception as e:
                logger.error(f"❌ Failed to queue demo video processing for challenge {challenge_id}: {str(e)}")
                # Don't fail the challenge creation if background processing fails to queue
        
        return challenge_id
    
    async def get_active_challenge(self) -> Optional[TodayChallengeResponse]:
        """Get today's active challenge"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        challenge = await self._get_db()[challenges_collection].find_one({
            "startTime": {"$lte": now},
            "endTime": {"$gt": now},
            "isActive": True
        })
        
        if not challenge:
            return None
        
        # Calculate time remaining
        time_remaining = challenge['endTime'] - now
        hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_remaining_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Get participant count
        participant_count = await self._get_db()[challenge_submissions_collection].count_documents({
            "challengeId": str(challenge['_id'])
        })
        
        # Prioritize processed demo video URL for mobile compatibility
        demo_video_url = challenge.get('processedDemoVideoURL') or challenge['demoVideoURL']
        
        return TodayChallengeResponse(
            id=str(challenge['_id']),
            title=challenge['title'],
            type=challenge['type'],
            timeRemaining=time_remaining_str,
            demoVideoURL=demo_video_url,
            points=challenge['points'],
            participantCount=participant_count,
            description=challenge['description'],
            difficulty=challenge['difficulty'],
            badgeName=challenge['badgeName'],
            badgeIconURL=challenge['badgeIconURL'],
            category=challenge.get('category'),
            tags=challenge.get('tags', [])
        )

    async def search_challenges(self, search_request: ChallengeSearchRequest) -> ChallengeListResponse:
        """Search and filter challenges"""
        db = self._get_db()
        
        # Build query
        query = {}
        
        if search_request.active_only:
            query["isActive"] = True
        
        if search_request.query:
            query["$or"] = [
                {"title": {"$regex": search_request.query, "$options": "i"}},
                {"description": {"$regex": search_request.query, "$options": "i"}},
                {"tags": {"$in": [search_request.query]}}
            ]
        
        if search_request.type:
            query["type"] = search_request.type
        
        if search_request.difficulty:
            query["difficulty"] = search_request.difficulty
        
        if search_request.categories:
            # Support multiple categories - challenge must have at least one of the requested categories
            query["categories"] = {"$in": search_request.categories}
        
        if search_request.tags:
            query["tags"] = {"$in": search_request.tags}
        
        # Calculate skip
        skip = (search_request.page - 1) * search_request.limit
        
        # Get challenges
        cursor = db[challenges_collection].find(query).skip(skip).limit(search_request.limit).sort("createdAt", -1)
        challenges = await cursor.to_list(length=search_request.limit)
        
        # Get total count
        total = await db[challenges_collection].count_documents(query)
        
        # Convert to response models
        challenge_responses = []
        for challenge in challenges:
            # Get participant count for each challenge
            participant_count = await db[challenge_submissions_collection].count_documents({
                "challengeId": str(challenge['_id'])
            })
            
            challenge['participantCount'] = participant_count
            
            # Convert ObjectId to string and handle scoringCriteria
            challenge['_id'] = str(challenge['_id'])
            if isinstance(challenge.get('scoringCriteria'), dict):
                challenge['scoringCriteria'] = ChallengeCriteria(**challenge['scoringCriteria'])
            
            challenge_responses.append(ChallengeResponse(**challenge))
        
        return ChallengeListResponse(
            challenges=challenge_responses,
            total=total,
            page=search_request.page,
            limit=search_request.limit
        )

    async def get_challenge_leaderboard(self, challenge_id: str, user_id: str) -> ChallengeLeaderboardResponse:
        """Get leaderboard for a specific challenge"""
        db = self._get_db()
        
        # Validate challenge exists
        challenge = await db[challenges_collection].find_one({"_id": ObjectId(challenge_id)})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Get submissions with scores, ordered by score descending
        pipeline = [
            {"$match": {"challengeId": challenge_id, "totalScore": {"$ne": None}}},
            {"$sort": {"totalScore": -1}},
            {"$limit": 50},  # Top 50
            {
                "$lookup": {
                    "from": "users",
                    "localField": "userId",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {"$unwind": "$user"}
        ]
        
        submissions = await db[challenge_submissions_collection].aggregate(pipeline).to_list(length=50)
        
        # Build leaderboard entries
        entries = []
        user_rank = None
        
        for rank, submission in enumerate(submissions, 1):
            user_profile = {
                "displayName": submission['user'].get('profile', {}).get('displayName', 'Unknown'),
                "avatarUrl": submission['user'].get('profile', {}).get('avatarUrl'),
                "level": submission['user'].get('stats', {}).get('level', 1)
            }
            
            entry = ChallengeLeaderboardEntry(
                rank=rank,
                userId=str(submission['userId']),
                userProfile=user_profile,
                score=submission.get('totalScore', 0),
                scoreBreakdown=submission.get('scoreBreakdown', {}),
                submittedAt=submission['submittedAt'],
                submissionId=str(submission['_id'])
            )
            entries.append(entry)
            
            # Track user's rank
            if str(submission['userId']) == user_id:
                user_rank = rank
        
        return ChallengeLeaderboardResponse(
            challengeId=challenge_id,
            challengeTitle=challenge['title'],
            entries=entries,
            total=len(entries),
            userRank=user_rank
        )

    async def get_challenge_categories(self) -> List[str]:
        """Get all challenge categories"""
        # Return predefined categories
        predefined_categories = [
            "hip hop",
            "ballet", 
            "trendy",
            "party",
            "sexy",
            "contemporary",
            "jazz",
            "street",
            "latin",
            "afro",
            "bollywood",
            "k-pop",
            "freestyle",
            "choreography"
        ]
        
        # Also get any additional categories from existing challenges
        db = self._get_db()
        existing_categories = await db[challenges_collection].distinct("categories")
        
        # Flatten the categories arrays and get unique values
        all_categories = set(predefined_categories)
        for category_list in existing_categories:
            if category_list:
                all_categories.update(category_list)
        
        return sorted(list(all_categories))

    async def get_challenge_tags(self) -> List[str]:
        """Get all challenge tags"""
        db = self._get_db()
        
        # Get all tags and flatten
        all_tags = await db[challenges_collection].distinct("tags")
        flat_tags = []
        for tag_list in all_tags:
            if tag_list:
                flat_tags.extend(tag_list)
        
        # Return unique tags
        return list(set(flat_tags))
    
    async def get_challenge_by_id(self, challenge_id: str) -> Optional[ChallengeResponse]:
        """Get a specific challenge by ID"""
        try:
            challenge = await self._get_db()[challenges_collection].find_one({"_id": ObjectId(challenge_id)})
            if not challenge:
                return None
            
            # Convert _id from ObjectId to string
            challenge['_id'] = str(challenge['_id'])
            
            # Prioritize processed demo video URL for mobile compatibility
            if 'processedDemoVideoURL' in challenge and challenge['processedDemoVideoURL']:
                challenge['demoVideoURL'] = challenge['processedDemoVideoURL']
            
            # Convert scoringCriteria dict back to ChallengeCriteria object
            if 'scoringCriteria' in challenge and isinstance(challenge['scoringCriteria'], dict):
                challenge['scoringCriteria'] = ChallengeCriteria(**challenge['scoringCriteria'])
            return ChallengeResponse(**challenge)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid challenge ID")
    
    async def list_challenges(self, page: int = 1, limit: int = 20, active_only: bool = True) -> ChallengeListResponse:
        """List challenges with pagination"""
        try:
            skip = (page - 1) * limit
            
            # Build query
            query = {}
            if active_only:
                query["isActive"] = True
            
            # Get total count
            total = await self._get_db()[challenges_collection].count_documents(query)
            
            # Get challenges
            challenges_cursor = self._get_db()[challenges_collection].find(query).sort("createdAt", -1).skip(skip).limit(limit)
            challenges = await challenges_cursor.to_list(length=limit)
            
            # Convert to response models
            challenge_responses = []
            for challenge in challenges:
                try:
                    # Convert _id from ObjectId to string
                    challenge['_id'] = str(challenge['_id'])
                    
                    # Prioritize processed demo video URL for mobile compatibility
                    if 'processedDemoVideoURL' in challenge and challenge['processedDemoVideoURL']:
                        challenge['demoVideoURL'] = challenge['processedDemoVideoURL']
                    
                    # Convert scoringCriteria dict back to ChallengeCriteria object
                    if 'scoringCriteria' in challenge and isinstance(challenge['scoringCriteria'], dict):
                        challenge['scoringCriteria'] = ChallengeCriteria(**challenge['scoringCriteria'])
                    challenge_responses.append(ChallengeResponse(**challenge))
                except Exception as e:
                    print(f"Error processing challenge {challenge.get('_id')}: {e}")
                    continue
            
            return ChallengeListResponse(
                challenges=challenge_responses,
                total=total,
                page=page,
                limit=limit
            )
        except Exception as e:
            print(f"Error in list_challenges: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def get_upcoming_challenges(self, days: int = 7) -> List[ChallengeResponse]:
        """Get upcoming challenges for the next N days"""
        now = datetime.utcnow()
        future_date = now + timedelta(days=days)
        
        challenges_cursor = self._get_db()[challenges_collection].find({
            "startTime": {"$gte": now, "$lte": future_date},
            "isActive": True
        }).sort("startTime", 1)
        
        challenges = await challenges_cursor.to_list(length=None)
        challenge_responses = []
        for challenge in challenges:
            # Convert _id from ObjectId to string
            challenge['_id'] = str(challenge['_id'])
            
            # Convert scoringCriteria dict back to ChallengeCriteria object
            if 'scoringCriteria' in challenge and isinstance(challenge['scoringCriteria'], dict):
                challenge['scoringCriteria'] = ChallengeCriteria(**challenge['scoringCriteria'])
            challenge_responses.append(ChallengeResponse(**challenge))
        return challenge_responses
    
    async def deactivate_expired_challenges(self) -> int:
        """Deactivate challenges that have ended"""
        now = datetime.utcnow()
        result = await self._get_db()[challenges_collection].update_many(
            {"endTime": {"$lt": now}, "isActive": True},
            {"$set": {"isActive": False, "updatedAt": now}}
        )
        return result.modified_count
    
    def _generate_video_url(self, file_key: str) -> str:
        """Generate video URL from S3 file key"""
        bucket_url = os.getenv('S3_BUCKET_URL')
        if bucket_url:
            return f"{bucket_url.rstrip('/')}/{file_key}"
        else:
            # Fallback to direct S3 URL
            region = os.getenv('AWS_REGION', 'us-east-1')
            bucket_name = os.getenv('S3_BUCKET_NAME')
            return f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_key}"
    
    async def update_challenge(self, challenge_id: str, challenge_data: ChallengeCreate, user_id: str) -> bool:
        """Update an existing challenge"""
        try:
            db = self._get_db()
            
            # Validate challenge exists
            existing_challenge = await db[challenges_collection].find_one({
                "_id": ObjectId(challenge_id)
            })
            
            if not existing_challenge:
                raise HTTPException(status_code=404, detail="Challenge not found")
            
            # Prepare update data
            now = datetime.utcnow()
            update_data = {
                "title": challenge_data.title,
                "description": challenge_data.description,
                "type": challenge_data.type,
                "difficulty": challenge_data.difficulty,
                "startTime": challenge_data.startTime,
                "endTime": challenge_data.endTime,
                "demoVideoFileKey": challenge_data.demoVideoFileKey,
                "points": challenge_data.points,
                "badgeName": challenge_data.badgeName,
                "badgeIconURL": challenge_data.badgeIconURL,
                "thumbnailURL": challenge_data.thumbnailURL,
                "scoringCriteria": challenge_data.scoringCriteria.dict() if challenge_data.scoringCriteria else None,
                "updatedAt": now,
                "updatedBy": user_id
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            # Update challenge
            result = await db[challenges_collection].update_one(
                {"_id": ObjectId(challenge_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error updating challenge: {e}")
            raise HTTPException(status_code=500, detail="Failed to update challenge")
    
    async def delete_challenge(self, challenge_id: str, user_id: str) -> bool:
        """Delete a challenge (soft delete by setting isActive to False)"""
        try:
            db = self._get_db()
            
            # Validate challenge exists
            existing_challenge = await db[challenges_collection].find_one({
                "_id": ObjectId(challenge_id)
            })
            
            if not existing_challenge:
                raise HTTPException(status_code=404, detail="Challenge not found")
            
            # Soft delete by setting isActive to False
            result = await db[challenges_collection].update_one(
                {"_id": ObjectId(challenge_id)},
                {
                    "$set": {
                        "isActive": False,
                        "deletedAt": datetime.utcnow(),
                        "deletedBy": user_id,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error deleting challenge: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete challenge")
    
    async def get_challenge_stats(self, challenge_id: str) -> dict:
        """Get comprehensive statistics for a challenge"""
        try:
            db = self._get_db()
            
            # Get challenge details
            challenge = await db[challenges_collection].find_one({
                "_id": ObjectId(challenge_id)
            })
            
            if not challenge:
                raise HTTPException(status_code=404, detail="Challenge not found")
            
            # Get submission statistics
            submission_stats = await db[challenge_submissions_collection].aggregate([
                {"$match": {"challengeId": challenge_id}},
                {"$group": {
                    "_id": None,
                    "totalSubmissions": {"$sum": 1},
                    "averageScore": {"$avg": "$totalScore"},
                    "topScore": {"$max": "$totalScore"},
                    "lowestScore": {"$min": "$totalScore"},
                    "completedAnalysis": {"$sum": {"$cond": ["$analysisComplete", 1, 0]}},
                    "pendingAnalysis": {"$sum": {"$cond": ["$analysisComplete", 0, 1]}}
                }}
            ]).to_list(length=1)
            
            stats = submission_stats[0] if submission_stats else {
                "totalSubmissions": 0,
                "averageScore": 0,
                "topScore": 0,
                "lowestScore": 0,
                "completedAnalysis": 0,
                "pendingAnalysis": 0
            }
            
            # Get user participation stats
            unique_participants = await db[challenge_submissions_collection].distinct(
                "userId", 
                {"challengeId": challenge_id}
            )
            
            # Get recent submissions (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_submissions = await db[challenge_submissions_collection].count_documents({
                "challengeId": challenge_id,
                "submittedAt": {"$gte": week_ago}
            })
            
            return {
                "challengeId": challenge_id,
                "challengeTitle": challenge.get("title", ""),
                "totalSubmissions": stats["totalSubmissions"],
                "uniqueParticipants": len(unique_participants),
                "averageScore": round(stats["averageScore"] or 0, 2),
                "topScore": stats["topScore"] or 0,
                "lowestScore": stats["lowestScore"] or 0,
                "completedAnalysis": stats["completedAnalysis"],
                "pendingAnalysis": stats["pendingAnalysis"],
                "recentSubmissions": recent_submissions,
                "challengeStatus": "active" if challenge.get("isActive") else "inactive",
                "startTime": challenge.get("startTime"),
                "endTime": challenge.get("endTime"),
                "createdAt": challenge.get("createdAt"),
                "lastUpdated": challenge.get("updatedAt")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error getting challenge stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to get challenge statistics")

    async def get_public_challenge_submissions(self, challenge_id: str, page: int = 1, limit: int = 20) -> PublicChallengeSubmissionsResponse:
        """Get public submissions for a specific challenge with video URLs"""
        try:
            # Validate challenge exists
            challenge = await self._get_db()[challenges_collection].find_one({
                "_id": ObjectId(challenge_id)
            })
            
            if not challenge:
                raise HTTPException(status_code=404, detail="Challenge not found")
            
            # Calculate skip for pagination
            skip = (page - 1) * limit
            
            # Get public submissions for this challenge
            submissions_cursor = self._get_db()[challenge_submissions_collection].find({
                "challengeId": challenge_id,
                "metadata.isPublic": True
            }).sort("timestamps.submittedAt", -1).skip(skip).limit(limit)
            
            submissions = await submissions_cursor.to_list(length=limit)
            
            # Get total count
            total = await self._get_db()[challenge_submissions_collection].count_documents({
                "challengeId": challenge_id,
                "metadata.isPublic": True
            })
            
            # Convert to response models
            submission_entries = []
            for submission in submissions:
                # Get user profile
                user = await self._get_db()[users_collection].find_one({
                    "_id": ObjectId(submission['userId'])
                })
                
                user_profile = {
                    "displayName": user.get("profile", {}).get("displayName", "Unknown"),
                    "avatarUrl": user.get("profile", {}).get("avatarUrl"),
                    "level": user.get("stats", {}).get("level", 1)
                } if user else {
                    "displayName": "Unknown",
                    "avatarUrl": None,
                    "level": 1
                }
                
                # Get submittedAt from timestamps
                submitted_at = submission.get('timestamps', {}).get('submittedAt')
                if not submitted_at:
                    # Fallback to direct field if timestamps structure doesn't exist
                    submitted_at = submission.get('submittedAt')
                
                # Create submission entry
                submission_entry = PublicSubmissionEntry(
                    _id=str(submission['_id']),
                    userId=str(submission['userId']),
                    userProfile=user_profile,
                    video=submission['video'],
                    analysis=submission['analysis'],
                    metadata=submission['metadata'],
                    submittedAt=submitted_at,
                    likes=submission.get('likes', []),
                    comments=submission.get('comments', []),
                    shares=submission.get('shares', 0)
                )
                submission_entries.append(submission_entry)
            
            return PublicChallengeSubmissionsResponse(
                challengeId=challenge_id,
                challengeTitle=challenge['title'],
                submissions=submission_entries,
                total=total,
                page=page,
                limit=limit
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get public submissions: {str(e)}")

    async def get_challenges_by_category(self, category: str, page: int = 1, limit: int = 20, active_only: bool = True) -> ChallengeListResponse:
        """Get challenges by specific category"""
        try:
            skip = (page - 1) * limit
            
            # Build query
            query = {"categories": {"$in": [category]}}
            if active_only:
                query["isActive"] = True
            
            # Get total count
            total = await self._get_db()[challenges_collection].count_documents(query)
            
            # Get challenges
            challenges_cursor = self._get_db()[challenges_collection].find(query).sort("createdAt", -1).skip(skip).limit(limit)
            challenges = await challenges_cursor.to_list(length=limit)
            
            # Convert to response models
            challenge_responses = []
            for challenge in challenges:
                try:
                    # Convert _id from ObjectId to string
                    challenge['_id'] = str(challenge['_id'])
                    
                    # Prioritize processed demo video URL for mobile compatibility
                    if 'processedDemoVideoURL' in challenge and challenge['processedDemoVideoURL']:
                        challenge['demoVideoURL'] = challenge['processedDemoVideoURL']
                    
                    # Convert scoringCriteria dict back to ChallengeCriteria object
                    if 'scoringCriteria' in challenge and isinstance(challenge['scoringCriteria'], dict):
                        challenge['scoringCriteria'] = ChallengeCriteria(**challenge['scoringCriteria'])
                    challenge_responses.append(ChallengeResponse(**challenge))
                except Exception as e:
                    print(f"Error processing challenge {challenge.get('_id')}: {e}")
                    continue
            
            return ChallengeListResponse(
                challenges=challenge_responses,
                total=total,
                page=page,
                limit=limit
            )
        except Exception as e:
            print(f"Error in get_challenges_by_category: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Global service instance
challenge_service = ChallengeService()

@challenge_router.get('/challenge/health')
def challenge_health():
    return {"status": "challenge service ok"}

@challenge_router.post('/api/challenges', response_model=dict)
async def create_challenge(
    challenge_data: ChallengeCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new challenge (admin only)"""
    # TODO: Add admin role check
    challenge_id = await challenge_service.create_challenge(challenge_data, user_id)
    return {"message": "Challenge created successfully", "challengeId": challenge_id}

@challenge_router.get('/api/challenges/today', response_model=Optional[TodayChallengeResponse])
async def get_today_challenge(user_id: str = Depends(get_current_user_id)):
    """Get today's active challenge"""
    return await challenge_service.get_active_challenge()

@challenge_router.get('/api/challenges/upcoming', response_model=List[ChallengeResponse])
async def get_upcoming_challenges(user_id: str = Depends(get_current_user_id), days: int = 7):
    """Get upcoming challenges for the next N days"""
    return await challenge_service.get_upcoming_challenges(days)

@challenge_router.get('/api/challenges/categories', response_model=List[str])
async def get_challenge_categories(user_id: str = Depends(get_current_user_id)):
    """Get all challenge categories"""
    return await challenge_service.get_challenge_categories()

@challenge_router.get('/api/challenges/tags', response_model=List[str])
async def get_challenge_tags(user_id: str = Depends(get_current_user_id)):
    """Get all challenge tags"""
    return await challenge_service.get_challenge_tags()

@challenge_router.get('/api/challenges/category/{category}', response_model=ChallengeListResponse)
async def get_challenges_by_category(
    category: str,
    page: int = 1,
    limit: int = 20,
    active_only: bool = True,
    user_id: str = Depends(get_current_user_id)
):
    """Get challenges by specific category"""
    return await challenge_service.get_challenges_by_category(category, page, limit, active_only)

@challenge_router.put('/api/challenges/{challenge_id}', response_model=dict)
async def update_challenge(
    challenge_id: str,
    challenge_data: ChallengeCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Update a challenge (admin only)"""
    # TODO: Add admin role check
    result = await challenge_service.update_challenge(challenge_id, challenge_data, user_id)
    return {"message": "Challenge updated successfully", "challengeId": challenge_id}

@challenge_router.delete('/api/challenges/{challenge_id}', response_model=dict)
async def delete_challenge(
    challenge_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a challenge (admin only)"""
    # TODO: Add admin role check
    result = await challenge_service.delete_challenge(challenge_id, user_id)
    return {"message": "Challenge deleted successfully", "challengeId": challenge_id}

@challenge_router.get('/api/challenges/{challenge_id}/stats', response_model=dict)
async def get_challenge_stats(
    challenge_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get challenge statistics"""
    stats = await challenge_service.get_challenge_stats(challenge_id)
    return stats

@challenge_router.get('/api/challenges/{challenge_id}', response_model=Optional[ChallengeResponse])
async def get_challenge(challenge_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific challenge by ID"""
    return await challenge_service.get_challenge_by_id(challenge_id)

@challenge_router.get('/api/challenges', response_model=ChallengeListResponse)
async def list_challenges(
    page: int = 1,
    limit: int = 20,
    active_only: bool = True,
    user_id: str = Depends(get_current_user_id)
):
    """List all challenges with pagination"""
    return await challenge_service.list_challenges(page, limit, active_only)

@challenge_router.post('/api/challenges/search', response_model=ChallengeListResponse)
async def search_challenges(
    search_request: ChallengeSearchRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Search and filter challenges"""
    return await challenge_service.search_challenges(search_request)

@challenge_router.get('/api/challenges/{challenge_id}/leaderboard', response_model=ChallengeLeaderboardResponse)
async def get_challenge_leaderboard(
    challenge_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get leaderboard for a specific challenge"""
    return await challenge_service.get_challenge_leaderboard(challenge_id, user_id)

@challenge_router.get('/api/challenges/{challenge_id}/public-submissions', response_model=PublicChallengeSubmissionsResponse)
async def get_public_challenge_submissions(
    challenge_id: str,
    page: int = 1,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id)
):
    """Get public submissions for a specific challenge with video URLs"""
    return await challenge_service.get_public_challenge_submissions(challenge_id, page, limit) 