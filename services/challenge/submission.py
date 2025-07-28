#!/usr/bin/env python3
"""
Challenge submission service for handling user submissions to challenges
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId
from infra.mongo import Database
from services.user.service import get_current_user_id
import logging

logger = logging.getLogger(__name__)

# Pydantic Models
class SubmissionCreate(BaseModel):
    """Request model for creating a submission"""
    sessionId: str = Field(..., description="ID of the dance session to submit")
    caption: Optional[str] = Field(None, max_length=500, description="Optional caption for the submission")
    tags: Optional[List[str]] = Field(None, description="Optional tags for the submission")

class SubmissionResponse(BaseModel):
    """Response model for submission data"""
    id: str = Field(..., alias="_id")
    userId: str
    challengeId: str
    sessionId: str
    totalScore: Optional[int] = None
    scoreBreakdown: Optional[Dict[str, int]] = None
    badgeAwarded: Optional[str] = None
    poseDataURL: Optional[str] = None
    analysisComplete: bool = False
    likes: List[str] = []
    comments: List[Dict] = []
    shares: int = 0
    submittedAt: datetime
    processedAt: Optional[datetime] = None
    userProfile: Dict

class SubmissionListResponse(BaseModel):
    """Response model for listing submissions"""
    submissions: List[SubmissionResponse]
    total: int
    page: int
    limit: int

class SubmissionService:
    """Service for handling challenge submissions"""
    
    def __init__(self):
        self.db = None
    
    def _get_db(self):
        if self.db is None:
            self.db = Database.get_database()
        return self.db
    
    async def submit_to_challenge(self, user_id: str, challenge_id: str, submission_data: SubmissionCreate) -> Dict:
        """
        Submit a dance session to a challenge
        """
        try:
            db = self._get_db()
            
            # Validate challenge exists and is active
            challenge = await db['challenges'].find_one({
                "_id": ObjectId(challenge_id),
                "isActive": True
            })
            
            if not challenge:
                raise HTTPException(status_code=404, detail="Challenge not found or not active")
            
            # Validate session exists and belongs to user
            session = await db['dance_sessions'].find_one({
                "_id": ObjectId(submission_data.sessionId),
                "userId": ObjectId(user_id)
            })
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found or doesn't belong to user")
            
            # Check if user already submitted to this challenge
            existing_submission = await db['challenge_submissions'].find_one({
                "userId": user_id,
                "challengeId": challenge_id
            })
            
            if existing_submission:
                raise HTTPException(status_code=400, detail="Already submitted to this challenge")
            
            # Get user profile for denormalization
            user = await db['users'].find_one({"_id": ObjectId(user_id)})
            user_profile = {
                "displayName": user.get("profile", {}).get("displayName", "Unknown"),
                "avatarUrl": user.get("profile", {}).get("avatarUrl"),
                "level": user.get("stats", {}).get("level", 1)
            }
            
            # Create submission
            now = datetime.utcnow()
            submission_doc = {
                "userId": user_id,
                "challengeId": challenge_id,
                "sessionId": submission_data.sessionId,
                "totalScore": None,  # Will be calculated by AI service
                "scoreBreakdown": None,
                "badgeAwarded": None,
                "poseDataURL": None,
                "analysisComplete": False,
                "likes": [],
                "comments": [],
                "shares": 0,
                "submittedAt": now,
                "processedAt": None,
                "userProfile": user_profile,
                "caption": submission_data.caption,
                "tags": submission_data.tags or []
            }
            
            result = await db['challenge_submissions'].insert_one(submission_doc)
            submission_id = str(result.inserted_id)
            
            # Update session with challenge link
            await db['dance_sessions'].update_one(
                {"_id": ObjectId(submission_data.sessionId)},
                {
                    "$set": {
                        "challengeId": challenge_id,
                        "challengeSubmissionId": submission_id,
                        "updatedAt": now
                    }
                }
            )
            
            # Update challenge submission count
            await db['challenges'].update_one(
                {"_id": ObjectId(challenge_id)},
                {
                    "$inc": {"totalSubmissions": 1},
                    "$set": {"updatedAt": now}
                }
            )
            
            logger.info(f"✅ User {user_id} submitted session {submission_data.sessionId} to challenge {challenge_id}")
            
            return {
                "submissionId": submission_id,
                "message": "Submission created successfully",
                "status": "pending_analysis"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error creating submission: {e}")
            raise HTTPException(status_code=500, detail="Failed to create submission")
    
    async def get_submission_by_id(self, submission_id: str, user_id: str) -> Optional[SubmissionResponse]:
        """Get a specific submission by ID"""
        try:
            db = self._get_db()
            
            submission = await db['challenge_submissions'].find_one({
                "_id": ObjectId(submission_id)
            })
            
            if not submission:
                return None
            
            # Convert ObjectId to string
            submission['_id'] = str(submission['_id'])
            
            return SubmissionResponse(**submission)
            
        except Exception as e:
            logger.error(f"❌ Error getting submission: {e}")
            return None
    
    async def get_challenge_submissions(self, challenge_id: str, page: int = 1, limit: int = 20) -> SubmissionListResponse:
        """Get submissions for a specific challenge"""
        try:
            db = self._get_db()
            skip = (page - 1) * limit
            
            # Get total count
            total = await db['challenge_submissions'].count_documents({
                "challengeId": challenge_id
            })
            
            # Get submissions
            submissions_cursor = db['challenge_submissions'].find({
                "challengeId": challenge_id
            }).sort("submittedAt", -1).skip(skip).limit(limit)
            
            submissions = await submissions_cursor.to_list(length=limit)
            
            # Convert ObjectIds to strings
            submission_responses = []
            for submission in submissions:
                submission['_id'] = str(submission['_id'])
                submission_responses.append(SubmissionResponse(**submission))
            
            return SubmissionListResponse(
                submissions=submission_responses,
                total=total,
                page=page,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting challenge submissions: {e}")
            raise HTTPException(status_code=500, detail="Failed to get submissions")
    
    async def get_user_submissions(self, user_id: str, page: int = 1, limit: int = 20) -> SubmissionListResponse:
        """Get submissions by a specific user"""
        try:
            db = self._get_db()
            skip = (page - 1) * limit
            
            # Get total count
            total = await db['challenge_submissions'].count_documents({
                "userId": user_id
            })
            
            # Get submissions
            submissions_cursor = db['challenge_submissions'].find({
                "userId": user_id
            }).sort("submittedAt", -1).skip(skip).limit(limit)
            
            submissions = await submissions_cursor.to_list(length=limit)
            
            # Convert ObjectIds to strings
            submission_responses = []
            for submission in submissions:
                submission['_id'] = str(submission['_id'])
                submission_responses.append(SubmissionResponse(**submission))
            
            return SubmissionListResponse(
                submissions=submission_responses,
                total=total,
                page=page,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting user submissions: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user submissions")

# Global service instance
submission_service = SubmissionService()

# Router
submission_router = APIRouter()

@submission_router.post('/api/challenges/{challenge_id}/submit', response_model=Dict)
async def submit_to_challenge(
    challenge_id: str,
    submission_data: SubmissionCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Submit a dance session to a challenge"""
    return await submission_service.submit_to_challenge(user_id, challenge_id, submission_data)

@submission_router.get('/api/challenges/{challenge_id}/submissions', response_model=SubmissionListResponse)
async def get_challenge_submissions(
    challenge_id: str,
    page: int = 1,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id)
):
    """Get submissions for a specific challenge"""
    return await submission_service.get_challenge_submissions(challenge_id, page, limit)

@submission_router.get('/api/submissions/{submission_id}', response_model=Optional[SubmissionResponse])
async def get_submission(
    submission_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific submission by ID"""
    return await submission_service.get_submission_by_id(submission_id, user_id)

@submission_router.get('/api/users/me/submissions', response_model=SubmissionListResponse)
async def get_my_submissions(
    page: int = 1,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id)
):
    """Get current user's submissions"""
    return await submission_service.get_user_submissions(user_id, page, limit) 