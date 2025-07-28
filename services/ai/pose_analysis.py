#!/usr/bin/env python3
"""
Pose Analysis Service for dance video analysis
"""

import asyncio
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from services.ai.models import PoseAnalysisResult, PoseFrame, PoseKeypoint, AnalysisRequest, AnalysisResponse
import logging

logger = logging.getLogger(__name__)

class PoseAnalysisService:
    """Service for analyzing pose data from dance videos"""
    
    def __init__(self):
        self.analysis_queue = {}  # In-memory queue for analysis status
    
    async def analyze_pose(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Analyze pose data from video URL
        For now, returns mock data for testing
        """
        try:
            logger.info(f"🎬 Starting pose analysis for submission {request.submission_id}")
            
            # Create initial response
            response = AnalysisResponse(
                submission_id=request.submission_id,
                status="processing",
                progress=0.0,
                created_at=datetime.utcnow()
            )
            
            # Store in queue for tracking
            self.analysis_queue[request.submission_id] = response
            
            # Simulate processing time
            await asyncio.sleep(2)  # Simulate processing
            
            # Generate mock pose data
            mock_pose_data = await self._generate_mock_pose_data(request)
            
            # Generate mock scores
            mock_scores = await self._generate_mock_scores(request)
            
            # Update response with results
            response.status = "completed"
            response.progress = 1.0
            response.pose_data_url = f"s3://pose-data/{request.submission_id}/pose_data.json"
            response.score_breakdown = mock_scores
            response.total_score = mock_scores.total_score
            response.feedback = await self._generate_mock_feedback(mock_scores)
            response.completed_at = datetime.utcnow()
            
            # 🚀 NEW: Update submission in database with analysis results
            try:
                await self._update_submission_in_database(request.submission_id, response)
                logger.info(f"✅ Updated submission {request.submission_id} in database")
            except Exception as e:
                logger.error(f"❌ Failed to update submission in database: {e}")
            
            logger.info(f"✅ Pose analysis completed for submission {request.submission_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in pose analysis: {e}")
            return AnalysisResponse(
                submission_id=request.submission_id,
                status="failed",
                error_message=str(e),
                created_at=datetime.utcnow()
            )
    
    async def get_analysis_status(self, submission_id: str) -> Optional[AnalysisResponse]:
        """Get current analysis status"""
        return self.analysis_queue.get(submission_id)
    
    async def _generate_mock_pose_data(self, request: AnalysisRequest) -> PoseAnalysisResult:
        """Generate mock pose data for testing"""
        frames = []
        total_frames = random.randint(30, 60)  # 1-2 seconds at 30fps
        
        for frame_num in range(total_frames):
            # Generate mock keypoints for a person
            keypoints = []
            keypoint_types = [
                "nose", "left_eye", "right_eye", "left_ear", "right_ear",
                "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
                "left_wrist", "right_wrist", "left_hip", "right_hip",
                "left_knee", "right_knee", "left_ankle", "right_ankle"
            ]
            
            for kp_type in keypoint_types:
                keypoint = PoseKeypoint(
                    x=random.uniform(0, 1),
                    y=random.uniform(0, 1),
                    confidence=random.uniform(0.7, 1.0),
                    keypoint_type=kp_type
                )
                keypoints.append(keypoint)
            
            frame = PoseFrame(
                frame_number=frame_num,
                timestamp=frame_num / 30.0,  # Assuming 30fps
                keypoints=keypoints,
                frame_confidence=random.uniform(0.8, 1.0)
            )
            frames.append(frame)
        
        return PoseAnalysisResult(
            submission_id=request.submission_id,
            total_frames=total_frames,
            frames_analyzed=total_frames,
            pose_frames=frames,
            analysis_confidence=random.uniform(0.85, 0.95),
            processing_time=random.uniform(1.5, 3.0),
            created_at=datetime.utcnow()
        )
    
    async def _generate_mock_scores(self, request: AnalysisRequest) -> 'ScoreBreakdown':
        """Generate mock scores for testing"""
        from services.ai.models import ScoreBreakdown
        
        # Generate realistic scores based on challenge type
        if request.challenge_type == "freestyle":
            balance = random.randint(15, 25)
            rhythm = random.randint(20, 30)
            smoothness = random.randint(18, 25)
            creativity = random.randint(12, 20)
        elif request.challenge_type == "static":
            balance = random.randint(20, 25)
            rhythm = random.randint(15, 25)
            smoothness = random.randint(15, 22)
            creativity = random.randint(8, 15)
        else:
            balance = random.randint(10, 20)
            rhythm = random.randint(15, 25)
            smoothness = random.randint(12, 20)
            creativity = random.randint(10, 18)
        
        return ScoreBreakdown(
            balance=balance,
            rhythm=rhythm,
            smoothness=smoothness,
            creativity=creativity
        )
    
    async def _generate_mock_feedback(self, scores: 'ScoreBreakdown') -> str:
        """Generate mock feedback based on scores"""
        feedback_parts = []
        
        if scores.balance >= 20:
            feedback_parts.append("Excellent balance control!")
        elif scores.balance >= 15:
            feedback_parts.append("Good balance, keep practicing.")
        else:
            feedback_parts.append("Work on your balance and stability.")
        
        if scores.rhythm >= 25:
            feedback_parts.append("Great rhythm and timing!")
        elif scores.rhythm >= 20:
            feedback_parts.append("Good rhythm, try to match the beat more closely.")
        else:
            feedback_parts.append("Focus on improving your rhythm and timing.")
        
        if scores.smoothness >= 20:
            feedback_parts.append("Very smooth movements!")
        elif scores.smoothness >= 15:
            feedback_parts.append("Good flow, work on making transitions smoother.")
        else:
            feedback_parts.append("Practice making your movements more fluid.")
        
        if scores.creativity >= 15:
            feedback_parts.append("Creative and unique style!")
        elif scores.creativity >= 10:
            feedback_parts.append("Good creativity, try more unique moves.")
        else:
            feedback_parts.append("Experiment with more creative movements.")
        
        return " ".join(feedback_parts)
    
    async def _update_submission_in_database(self, submission_id: str, analysis_response: 'AnalysisResponse') -> None:
        """Update submission in database with analysis results"""
        try:
            from infra.mongo import Database
            from bson import ObjectId
            from datetime import datetime
            
            db = Database.get_database()
            
            update_data = {
                "analysisComplete": True,
                "processedAt": datetime.utcnow()
            }
            
            # Update with score breakdown if available
            if analysis_response.score_breakdown:
                update_data["scoreBreakdown"] = analysis_response.score_breakdown.dict()
                update_data["totalScore"] = analysis_response.total_score
            
            # Update with pose data URL if available
            if analysis_response.pose_data_url:
                update_data["poseDataURL"] = analysis_response.pose_data_url
            
            # Update submission
            result = await db['challenge_submissions'].update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": update_data}
            )
            
            logger.info(f"✅ Database update result: {result.modified_count} documents modified for submission {submission_id}")
            
        except Exception as e:
            logger.error(f"❌ Error updating submission in database: {e}")
            raise

# Global service instance
pose_analysis_service = PoseAnalysisService() 