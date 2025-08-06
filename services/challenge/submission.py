#!/usr/bin/env python3
"""
Challenge submission service for handling user submissions to challenges
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from bson import ObjectId
from infra.mongo import Database
from services.user.service import get_current_user_id
from services.ai.pose_analysis import pose_analysis_service
from services.ai.models import AnalysisRequest
import logging
from services.challenge.models import (
    UnifiedSubmissionRequest, UnifiedSubmissionResponse, VideoData, AnalysisData, SubmissionMetadata
)

logger = logging.getLogger(__name__)

# Pydantic Models
class SubmissionCreate(BaseModel):
    """Request model for creating a submission"""
    sessionId: str = Field(..., description="ID of the dance session to submit")
    caption: Optional[str] = Field(None, max_length=500, description="Optional caption for the submission")
    tags: Optional[List[str]] = Field(None, description="Optional tags for the submission")

class DirectUploadRequest(BaseModel):
    """Request model for direct video upload to challenge"""
    video_url: str = Field(..., description="URL of the uploaded video")
    caption: Optional[str] = Field(None, max_length=500, description="Optional caption for the submission")
    tags: Optional[List[str]] = Field(None, description="Optional tags for the submission")
    location: Optional[str] = Field(None, description="Optional location")
    isPublic: bool = Field(True, description="Whether the submission is public")
    sharedToFeed: bool = Field(True, description="Whether to share to feed")

class ChallengeUploadRequest(BaseModel):
    """Request model for challenge video upload (S3 flow)"""
    file_key: str = Field(..., description="S3 file key of the uploaded video")
    file_url: str = Field(..., description="S3 file URL of the uploaded video")
    caption: Optional[str] = Field(None, max_length=500, description="Optional caption for the submission")
    tags: Optional[List[str]] = Field(None, description="Optional tags for the submission")
    location: Optional[str] = Field(None, description="Optional location")
    isPublic: bool = Field(True, description="Whether the submission is public")
    sharedToFeed: bool = Field(True, description="Whether to share to feed")

class SubmissionMetadataRequest(BaseModel):
    """Request model for updating submission metadata after analysis"""
    caption: Optional[str] = Field(None, max_length=500, description="Caption for the submission")
    tags: Optional[List[str]] = Field(None, description="Tags for the submission")
    location: Optional[str] = Field(None, description="Location where dance was performed")
    isPublic: bool = Field(True, description="Whether the submission is public")
    sharedToFeed: bool = Field(True, description="Whether to share to feed")
    highlightText: Optional[str] = Field(None, max_length=200, description="Highlight text for the submission")

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
    """Response model for list of submissions"""
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
    
    async def submit_challenge_unified(self, user_id: str, challenge_id: str, submission_request: UnifiedSubmissionRequest) -> UnifiedSubmissionResponse:
        """
        Unified challenge submission - handles video upload, analysis, and metadata in one call
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
            
            # Process video upload
            video_data = await self._process_video_upload(
                submission_request.video_file, user_id, challenge_id, submission_request.video_duration_seconds
            )
            
            # Create session first
            now = datetime.utcnow()
            session_doc = {
                "userId": ObjectId(user_id),
                "startTime": now,
                "endTime": now,
                "status": "completed",
                "durationMinutes": int(video_data.duration / 60) if video_data.duration else 1,  # Convert seconds to minutes
                "caloriesBurned": 0,
                "style": "freestyle",
                "sessionType": "challenge",
                "videoURL": video_data.url,
                "videoFileKey": video_data.file_key,
                "thumbnailURL": None,
                "thumbnailFileKey": None,
                "location": submission_request.metadata.location,
                "highlightText": submission_request.metadata.highlightText,
                "tags": submission_request.metadata.tags or [],
                "score": None,
                "stars": None,
                "rating": None,
                "isPublic": submission_request.metadata.isPublic,
                "sharedToFeed": submission_request.metadata.sharedToFeed,
                "remixable": False,
                "promptUsed": None,
                "inspirationSessionId": None,
                "challengeId": challenge_id,
                "challengeSubmissionId": None,  # Will be set after submission creation
                "createdAt": now,
                "updatedAt": now
            }
            
            # Insert session
            session_result = await db['dance_sessions'].insert_one(session_doc)
            session_id = str(session_result.inserted_id)
            
            # Create submission with new unified structure
            submission_doc = {
                "userId": user_id,
                "challengeId": challenge_id,
                "sessionId": session_id,
                "video": video_data.dict(),
                "analysis": {
                    "status": "pending",
                    "score": None,
                    "breakdown": None,
                    "feedback": None,
                    "pose_data_url": None,
                    "confidence": None
                },
                "metadata": submission_request.metadata.dict(),
                "userProfile": user_profile,
                "timestamps": {
                    "submittedAt": now,
                    "processedAt": None,
                    "analyzedAt": None
                },
                "likes": [],
                "comments": [],
                "shares": 0
            }
            
            submission_result = await db['challenge_submissions'].insert_one(submission_doc)
            submission_id = str(submission_result.inserted_id)
            
            # Update session with submission link
            await db['dance_sessions'].update_one(
                {"_id": session_result.inserted_id},
                {
                    "$set": {
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
            
            # Update user stats for challenge submission
            await self._update_user_stats_from_challenge(db, user_id, video_data, challenge)
            
            # 🚀 Trigger AI analysis automatically and wait for completion
            analysis_completed = False
            try:
                # Run AI analysis synchronously for unified submission
                analysis_result = await self._run_ai_analysis_sync(submission_id, session_doc, challenge)
                if analysis_result:
                    # Update submission with analysis results
                    await self._update_submission_with_analysis(submission_id, analysis_result)
                    analysis_completed = True
                    logger.info(f"✅ AI analysis completed for unified submission {submission_id}")
                else:
                    logger.warning(f"⚠️ AI analysis returned no result for unified submission {submission_id}")
            except Exception as e:
                logger.error(f"⚠️ AI analysis failed for unified submission {submission_id}: {e}")
                # Don't fail the submission if AI analysis fails
            
            # Get updated submission data if analysis completed
            if analysis_completed:
                updated_submission = await db['challenge_submissions'].find_one({"_id": ObjectId(submission_id)})
                if updated_submission:
                    submission_doc["analysis"] = updated_submission["analysis"]
                    submission_doc["timestamps"] = updated_submission["timestamps"]
            
            logger.info(f"✅ User {user_id} submitted unified challenge {challenge_id}")
            
            # Create timestamps with proper datetime objects
            timestamps = {
                "submittedAt": now,
                "processedAt": submission_doc["timestamps"].get("processedAt"),
                "analyzedAt": submission_doc["timestamps"].get("analyzedAt")
            }
            
            return UnifiedSubmissionResponse(
                _id=submission_id,  # Use _id alias
                challengeId=challenge_id,
                userId=user_id,
                video=video_data,
                analysis=submission_doc["analysis"],
                metadata=submission_request.metadata,
                userProfile=user_profile,
                timestamps=timestamps,
                likes=[],
                comments=[],
                shares=0
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error in unified submission: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit challenge")

    async def update_submission_metadata(self, user_id: str, submission_id: str, metadata: SubmissionMetadataRequest) -> Dict:
        """Update submission metadata after analysis is complete"""
        try:
            db = self._get_db()
            
            # Validate submission exists and belongs to user
            submission = await db['challenge_submissions'].find_one({
                "_id": ObjectId(submission_id),
                "userId": user_id
            })
            
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found or doesn't belong to user")
            
            # Update submission metadata
            update_data = {
                "metadata.caption": metadata.caption,
                "metadata.tags": metadata.tags or [],
                "metadata.location": metadata.location,
                "metadata.isPublic": metadata.isPublic,
                "metadata.sharedToFeed": metadata.sharedToFeed,
                "metadata.highlightText": metadata.highlightText,
                "updatedAt": datetime.utcnow()
            }
            
            await db['challenge_submissions'].update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": update_data}
            )
            
            # Update session metadata as well
            session_id = submission.get("sessionId")
            if session_id:
                session_update_data = {
                    "location": metadata.location,
                    "highlightText": metadata.highlightText,
                    "tags": metadata.tags or [],
                    "isPublic": metadata.isPublic,
                    "sharedToFeed": metadata.sharedToFeed,
                    "updatedAt": datetime.utcnow()
                }
                
                await db['dance_sessions'].update_one(
                    {"_id": ObjectId(session_id)},
                    {"$set": session_update_data}
                )
            
            logger.info(f"✅ Updated metadata for submission {submission_id}")
            
            return {
                "submissionId": submission_id,
                "message": "Submission metadata updated successfully",
                "status": "completed"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error updating submission metadata: {e}")
            raise HTTPException(status_code=500, detail="Failed to update submission metadata")

    async def _trigger_ai_analysis(self, submission_id: str, session: dict, challenge: dict) -> None:
        """Trigger AI analysis for a submission"""
        try:
            # Get video URL from session
            video_url = session.get("videoURL")
            if not video_url:
                logger.warning(f"No video URL found for session {session.get('_id')}")
                return
            
            # Create analysis request
            analysis_request = AnalysisRequest(
                submission_id=submission_id,
                video_url=video_url,
                challenge_type=challenge.get("type", "freestyle"),
                target_bpm=None  # Could be extracted from challenge metadata
            )
            
            # Trigger pose analysis (this will run asynchronously)
            analysis_result = await pose_analysis_service.analyze_pose(analysis_request)
            
            # Update submission with analysis results
            await self._update_submission_with_analysis(submission_id, analysis_result)
            
        except Exception as e:
            logger.error(f"❌ Error in AI analysis trigger: {e}")
            raise

    async def _update_submission_with_analysis(self, submission_id: str, analysis_result) -> None:
        """Update submission with AI analysis results"""
        try:
            db = self._get_db()
            
            # Handle both dict and AnalysisResponse objects
            if hasattr(analysis_result, 'total_score'):
                # It's an AnalysisResponse object
                update_data = {
                    "analysis.status": "completed",
                    "analysis.score": analysis_result.total_score,
                    "analysis.breakdown": analysis_result.score_breakdown.dict() if analysis_result.score_breakdown else None,
                    "analysis.feedback": analysis_result.feedback,
                    "analysis.pose_data_url": analysis_result.pose_data_url,
                    "analysis.confidence": 0.0,  # Default confidence
                    "timestamps.analyzedAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                }
            else:
                # It's a dictionary (legacy support)
                update_data = {
                    "analysis.status": "completed",
                    "analysis.score": analysis_result.get("total_score"),
                    "analysis.breakdown": analysis_result.get("score_breakdown"),
                    "analysis.feedback": analysis_result.get("feedback"),
                    "analysis.pose_data_url": analysis_result.get("pose_data_url"),
                    "analysis.confidence": analysis_result.get("confidence", 0.0),
                    "timestamps.analyzedAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                }
            
            # Update submission
            result = await db['challenge_submissions'].update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": update_data}
            )
            
            logger.info(f"✅ Updated submission {submission_id} with analysis results: {result.modified_count} documents modified")
            
        except Exception as e:
            logger.error(f"❌ Error updating submission with analysis: {e}")
            raise

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
            }).sort("timestamps.submittedAt", -1).skip(skip).limit(limit)
            
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
            }).sort("timestamps.submittedAt", -1).skip(skip).limit(limit)
            
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

    async def _process_video_upload(self, video_file: str, user_id: str, challenge_id: str, provided_duration: Optional[int] = None) -> VideoData:
        """
        Process video file upload (URL, S3 file key, or base64) and return video data
        """
        import uuid
        
        try:
            # Use provided duration if available, otherwise extract from video
            if provided_duration and provided_duration > 0:
                duration = provided_duration
            else:
                duration = None  # Will be extracted from video
            
            # Check if it's a URL
            if video_file.startswith('http'):
                # It's a URL, use it directly
                file_key = f"challenges/{user_id}/{challenge_id}/external_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
                # Extract duration from URL video if not provided
                if not duration:
                    duration = await self._extract_video_duration_from_url(video_file)
                return VideoData(
                    url=video_file,
                    file_key=file_key,
                    duration=duration,
                    size_mb=25.0  # Default size
                )
            
            # Check if it's an S3 file key
            elif video_file.startswith('challenges/'):
                # It's an S3 file key, construct the URL
                file_url = f"https://idanceshreyansh.s3.ap-south-1.amazonaws.com/{video_file}"
                # Extract duration from S3 video if not provided
                if not duration:
                    duration = await self._extract_video_duration_from_url(file_url)
                return VideoData(
                    url=file_url,
                    file_key=video_file,
                    duration=duration,
                    size_mb=25.0  # Default size
                )
            
            # Otherwise, assume it's base64 (original logic)
            else:
                import base64
                
                # Generate unique file key
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                unique_id = str(uuid.uuid4())[:8]
                file_key = f"challenges/{user_id}/{challenge_id}/{timestamp}_{unique_id}.mp4"
                
                # Decode base64 and upload to S3
                video_bytes = base64.b64decode(video_file)
                
                # Upload to S3 (simplified for now)
                # In production, use the S3 service
                file_url = f"https://bucket.s3.amazonaws.com/{file_key}"
                
                # Calculate video duration and size (simplified)
                size_mb = len(video_bytes) / (1024 * 1024)
                # Extract duration from video bytes if not provided
                if not duration:
                    duration = await self._extract_video_duration_from_bytes(video_bytes)
                
                return VideoData(
                    url=file_url,
                    file_key=file_key,
                    duration=duration,
                    size_mb=size_mb
                )
            
        except Exception as e:
            logger.error(f"❌ Error processing video upload: {e}")
            raise HTTPException(status_code=400, detail="Invalid video file")

    async def _extract_video_duration_from_url(self, video_url: str) -> int:
        """Extract video duration from URL using ffprobe"""
        try:
            import subprocess
            import json
            
            # Use ffprobe to get video duration
            cmd = [
                'ffprobe', 
                '-v', 'quiet', 
                '-print_format', 'json', 
                '-show_format', 
                video_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration_seconds = float(data['format']['duration'])
                return int(duration_seconds)
            else:
                logger.warning(f"Failed to extract duration from {video_url}: {result.stderr}")
                return 60  # Default fallback
                
        except Exception as e:
            logger.warning(f"Error extracting video duration from {video_url}: {e}")
            return 60  # Default fallback

    async def _extract_video_duration_from_bytes(self, video_bytes: bytes) -> int:
        """Extract video duration from video bytes using ffprobe"""
        try:
            import subprocess
            import json
            import tempfile
            import os
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(video_bytes)
                temp_path = temp_file.name
            
            try:
                # Use ffprobe to get video duration
                cmd = [
                    'ffprobe', 
                    '-v', 'quiet', 
                    '-print_format', 'json', 
                    '-show_format', 
                    temp_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    duration_seconds = float(data['format']['duration'])
                    return int(duration_seconds)
                else:
                    logger.warning(f"Failed to extract duration from video bytes: {result.stderr}")
                    return 60  # Default fallback
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.warning(f"Error extracting video duration from bytes: {e}")
            return 60  # Default fallback

    async def _run_ai_analysis_sync(self, submission_id: str, session: dict, challenge: dict):
        """Run AI analysis synchronously and return results"""
        try:
            # Get video URL from session
            video_url = session.get("videoURL")
            if not video_url:
                logger.warning(f"No video URL found for session {session.get('_id')}")
                return None
            
            # Import AI service
            from services.ai.pose_analysis import pose_analysis_service
            from services.ai.models import AnalysisRequest
            
            # Create analysis request
            analysis_request = AnalysisRequest(
                submission_id=submission_id,
                video_url=video_url,
                challenge_type=challenge.get("type", "freestyle"),
                target_bpm=None  # Could be extracted from challenge metadata
            )
            
            # Run pose analysis synchronously
            analysis_result = await pose_analysis_service.analyze_pose(analysis_request)
            
            logger.info(f"✅ Synchronous AI analysis completed for submission {submission_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error in synchronous AI analysis: {e}")
            return None

    async def _update_user_stats_from_challenge(self, db, user_id: str, video_data: VideoData, challenge: dict):
        """Updates user stats based on the challenge type and video duration."""
        try:
            user = await db['users'].find_one({"_id": ObjectId(user_id)})
            if not user:
                logger.warning(f"User {user_id} not found for stats update.")
                return

            challenge_type = challenge.get("type", "freestyle")
            duration_seconds = video_data.duration or 0
            duration_minutes = int(duration_seconds / 60) if duration_seconds > 0 else 1

            # Get current date for weekly activity
            today = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Get current user stats
            user_stats = await db['user_stats'].find_one({'_id': ObjectId(user_id)}) or {}
            weekly_activity = user_stats.get('weeklyActivity', [])
            
            # Update weekly activity for today
            today_found = False
            for activity in weekly_activity:
                if activity['date'] == today:
                    activity['sessionsCount'] += 1
                    today_found = True
                    break
            
            if not today_found:
                weekly_activity.append({'date': today, 'sessionsCount': 1})
            
            # Keep only last 7 days
            today_date = datetime.strptime(today, '%Y-%m-%d').date()
            seven_days_ago = today_date - timedelta(days=6)
            weekly_activity = [
                activity for activity in weekly_activity 
                if datetime.strptime(activity['date'], '%Y-%m-%d').date() >= seven_days_ago
            ]

            # Update challenge-specific stats
            if challenge_type == "freestyle":
                # For freestyle, duration is directly related to calories burned
                calories_burned = int(duration_minutes * 5) # Example: 5 calories per minute
                await db['user_stats'].update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$inc": {
                            "totalKcal": calories_burned,
                            "totalTimeMinutes": duration_minutes,
                            "totalSessions": 1
                        },
                        "$set": {
                            "updatedAt": datetime.utcnow(),
                            "mostPlayedStyle": "freestyle",
                            "weeklyActivity": weekly_activity
                        }
                    },
                    upsert=True
                )
                logger.info(f"✅ Updated user {user_id} stats for freestyle challenge.")
            elif challenge_type == "static":
                # For static challenges, less calories but still counts as activity
                calories_burned = int(duration_minutes * 3) # Example: 3 calories per minute
                await db['user_stats'].update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$inc": {
                            "totalKcal": calories_burned,
                            "totalTimeMinutes": duration_minutes,
                            "totalSessions": 1
                        },
                        "$set": {
                            "updatedAt": datetime.utcnow(),
                            "mostPlayedStyle": "static",
                            "weeklyActivity": weekly_activity
                        }
                    },
                    upsert=True
                )
                logger.info(f"✅ Updated user {user_id} stats for static challenge.")
            else:
                # For other challenge types, still count as activity
                calories_burned = int(duration_minutes * 4) # Example: 4 calories per minute
                await db['user_stats'].update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$inc": {
                            "totalKcal": calories_burned,
                            "totalTimeMinutes": duration_minutes,
                            "totalSessions": 1
                        },
                        "$set": {
                            "updatedAt": datetime.utcnow(),
                            "mostPlayedStyle": challenge_type,
                            "weeklyActivity": weekly_activity
                        }
                    },
                    upsert=True
                )
                logger.info(f"✅ Updated user {user_id} stats for {challenge_type} challenge.")

        except Exception as e:
            logger.error(f"❌ Error updating user stats from challenge: {e}")
            raise

# Global service instance
submission_service = SubmissionService()

# Router
submission_router = APIRouter()

@submission_router.post('/api/challenges/{challenge_id}/submit-unified', response_model=UnifiedSubmissionResponse)
async def submit_challenge_unified(
    challenge_id: str,
    submission_request: UnifiedSubmissionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Unified challenge submission - handles video upload, analysis, and metadata in one call"""
    return await submission_service.submit_challenge_unified(user_id, challenge_id, submission_request)

@submission_router.put('/api/submissions/{submission_id}/metadata', response_model=Dict)
async def update_submission_metadata(
    submission_id: str,
    metadata: SubmissionMetadataRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Update submission metadata after analysis is complete"""
    return await submission_service.update_submission_metadata(user_id, submission_id, metadata)

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
    """Get a specific submission"""
    return await submission_service.get_submission_by_id(submission_id, user_id)

@submission_router.get('/api/users/{user_id}/submissions', response_model=SubmissionListResponse)
async def get_user_submissions(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get all submissions by a user"""
    return await submission_service.get_user_submissions(user_id, page, limit) 