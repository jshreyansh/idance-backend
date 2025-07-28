from fastapi import APIRouter, HTTPException, Depends
from services.challenge.models import Challenge, ChallengeCreate, ChallengeResponse, ChallengeListResponse, TodayChallengeResponse, ChallengeCriteria
from services.user.service import get_current_user_id
from infra.mongo import Database
from datetime import datetime, timedelta
from bson import ObjectId
from typing import List, Optional
import os

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
        
        # Generate demo video URL from file key
        demo_video_url = self._generate_video_url(challenge_data.demoVideoFileKey)
        
        now = datetime.utcnow()
        challenge_doc = {
            "title": challenge_data.title,
            "description": challenge_data.description,
            "type": challenge_data.type,
            "difficulty": challenge_data.difficulty,
            "startTime": challenge_data.startTime,
            "endTime": challenge_data.endTime,
            "demoVideoURL": demo_video_url,
            "demoVideoFileKey": challenge_data.demoVideoFileKey,
            "thumbnailURL": challenge_data.thumbnailURL,
            "points": challenge_data.points,
            "badgeName": challenge_data.badgeName,
            "badgeIconURL": challenge_data.badgeIconURL,
            "scoringCriteria": challenge_data.scoringCriteria.dict(),
            "isActive": True,
            "createdBy": user_id,
            "createdAt": now,
            "updatedAt": now,
            "totalSubmissions": 0,
            "averageScore": 0.0,
            "topScore": 0
        }
        
        result = await self._get_db()['challenges'].insert_one(challenge_doc)
        return str(result.inserted_id)
    
    async def get_active_challenge(self) -> Optional[TodayChallengeResponse]:
        """Get today's active challenge"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        challenge = await self._get_db()['challenges'].find_one({
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
        participant_count = await self._get_db()['challenge_submissions'].count_documents({
            "challengeId": str(challenge['_id'])
        })
        
        return TodayChallengeResponse(
            id=str(challenge['_id']),
            title=challenge['title'],
            type=challenge['type'],
            timeRemaining=time_remaining_str,
            demoVideoURL=challenge['demoVideoURL'],
            points=challenge['points'],
            participantCount=participant_count,
            description=challenge['description'],
            difficulty=challenge['difficulty'],
            badgeName=challenge['badgeName'],
            badgeIconURL=challenge['badgeIconURL']
        )
    
    async def get_challenge_by_id(self, challenge_id: str) -> Optional[ChallengeResponse]:
        """Get a specific challenge by ID"""
        try:
            challenge = await self._get_db()['challenges'].find_one({"_id": ObjectId(challenge_id)})
            if not challenge:
                return None
            
            # Convert _id from ObjectId to string
            challenge['_id'] = str(challenge['_id'])
            
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
            total = await self._get_db()['challenges'].count_documents(query)
            
            # Get challenges
            challenges_cursor = self._get_db()['challenges'].find(query).sort("createdAt", -1).skip(skip).limit(limit)
            challenges = await challenges_cursor.to_list(length=limit)
            
            # Convert to response models
            challenge_responses = []
            for challenge in challenges:
                try:
                    # Convert _id from ObjectId to string
                    challenge['_id'] = str(challenge['_id'])
                    
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
        
        challenges_cursor = self._get_db()['challenges'].find({
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
        result = await self._get_db()['challenges'].update_many(
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
            existing_challenge = await db['challenges'].find_one({
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
            result = await db['challenges'].update_one(
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
            existing_challenge = await db['challenges'].find_one({
                "_id": ObjectId(challenge_id)
            })
            
            if not existing_challenge:
                raise HTTPException(status_code=404, detail="Challenge not found")
            
            # Soft delete by setting isActive to False
            result = await db['challenges'].update_one(
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
            challenge = await db['challenges'].find_one({
                "_id": ObjectId(challenge_id)
            })
            
            if not challenge:
                raise HTTPException(status_code=404, detail="Challenge not found")
            
            # Get submission statistics
            submission_stats = await db['challenge_submissions'].aggregate([
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
            unique_participants = await db['challenge_submissions'].distinct(
                "userId", 
                {"challengeId": challenge_id}
            )
            
            # Get recent submissions (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_submissions = await db['challenge_submissions'].count_documents({
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
    """List challenges with pagination"""
    return await challenge_service.list_challenges(page, limit, active_only) 