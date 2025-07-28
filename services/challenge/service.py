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
            
            return ChallengeResponse(**challenge)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid challenge ID")
    
    async def list_challenges(self, page: int = 1, limit: int = 20, active_only: bool = True) -> ChallengeListResponse:
        """List challenges with pagination"""
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
            challenge_responses.append(ChallengeResponse(**challenge))
        
        return ChallengeListResponse(
            challenges=challenge_responses,
            total=total,
            page=page,
            limit=limit
        )
    
    async def get_upcoming_challenges(self, days: int = 7) -> List[ChallengeResponse]:
        """Get upcoming challenges for the next N days"""
        now = datetime.utcnow()
        future_date = now + timedelta(days=days)
        
        challenges_cursor = self._get_db()['challenges'].find({
            "startTime": {"$gte": now, "$lte": future_date},
            "isActive": True
        }).sort("startTime", 1)
        
        challenges = await challenges_cursor.to_list(length=None)
        return [ChallengeResponse(**challenge) for challenge in challenges]
    
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
async def get_today_challenge():
    """Get today's active challenge"""
    return await challenge_service.get_active_challenge()

@challenge_router.get('/api/challenges/{challenge_id}', response_model=Optional[ChallengeResponse])
async def get_challenge(challenge_id: str):
    """Get a specific challenge by ID"""
    return await challenge_service.get_challenge_by_id(challenge_id)

@challenge_router.get('/api/challenges', response_model=ChallengeListResponse)
async def list_challenges(
    page: int = 1,
    limit: int = 20,
    active_only: bool = True
):
    """List challenges with pagination"""
    return await challenge_service.list_challenges(page, limit, active_only)

@challenge_router.get('/api/challenges/upcoming', response_model=List[ChallengeResponse])
async def get_upcoming_challenges(days: int = 7):
    """Get upcoming challenges for the next N days"""
    return await challenge_service.get_upcoming_challenges(days) 