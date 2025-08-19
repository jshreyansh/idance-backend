#!/usr/bin/env python3
"""
Challenge Scoring Integration Service using MMPose
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

from .mmpose import mmpose_service
from .mmpose.models import ChallengeAnalysisRequest, ChallengeAnalysisResponse
from services.challenge.models import AnalysisData

logger = logging.getLogger(__name__)

class ChallengeScoringService:
    """Service for integrating MMPose scoring with challenges"""
    
    def __init__(self):
        self.scoring_queue = {}
    
    async def analyze_challenge_submission(self, submission_id: str, video_url: str, 
                                         challenge_type: str, challenge_difficulty: str,
                                         target_bpm: Optional[int] = None) -> AnalysisData:
        """Analyze a challenge submission using MMPose"""
        try:
            logger.info(f"🎯 Starting MMPose challenge analysis for submission {submission_id}")
            
            # Create analysis request
            request = ChallengeAnalysisRequest(
                submission_id=submission_id,
                video_url=video_url,
                challenge_type=challenge_type,
                challenge_difficulty=challenge_difficulty,
                target_bpm=target_bpm
            )
            
            # Start MMPose analysis
            response = await mmpose_service.analyze_challenge_submission(request)
            
            if response.status == "completed" and response.analysis_result:
                # Convert MMPose result to AnalysisData
                analysis_data = self._convert_mmpose_to_analysis_data(response.analysis_result)
                logger.info(f"✅ MMPose analysis completed for submission {submission_id}")
                return analysis_data
            else:
                logger.error(f"❌ MMPose analysis failed for submission {submission_id}: {response.error_message}")
                return self._get_fallback_analysis_data(submission_id, response.error_message)
                
        except Exception as e:
            logger.error(f"❌ Error in challenge scoring: {e}")
            return self._get_fallback_analysis_data(submission_id, str(e))
    
    def _convert_mmpose_to_analysis_data(self, mmpose_result) -> AnalysisData:
        """Convert MMPose analysis result to AnalysisData"""
        try:
            scoring_result = mmpose_result.scoring_result
            
            # Create score breakdown
            score_breakdown = {
                "technique": scoring_result.technique_score,
                "rhythm": scoring_result.rhythm_score,
                "expression": scoring_result.expression_score,
                "difficulty": scoring_result.difficulty_score
            }
            
            # Generate feedback
            feedback = self._generate_feedback(scoring_result, mmpose_result)
            
            return AnalysisData(
                status="completed",
                score=scoring_result.total_score,
                breakdown=score_breakdown,
                feedback=feedback,
                pose_data_url=f"s3://pose-data/{mmpose_result.submission_id}/mmpose_data.json",
                confidence=scoring_result.confidence
            )
            
        except Exception as e:
            logger.error(f"❌ Error converting MMPose result: {e}")
            return self._get_fallback_analysis_data(mmpose_result.submission_id, str(e))
    
    def _generate_feedback(self, scoring_result, mmpose_result) -> str:
        """Generate human-readable feedback from MMPose results"""
        try:
            feedback_parts = []
            
            # Technique feedback
            if scoring_result.technique_score >= 80:
                feedback_parts.append("Excellent technique! Your form and execution are outstanding.")
            elif scoring_result.technique_score >= 60:
                feedback_parts.append("Good technique overall. Focus on refining your form and precision.")
            else:
                feedback_parts.append("Work on improving your technique. Focus on proper form and alignment.")
            
            # Rhythm feedback
            if scoring_result.rhythm_score >= 80:
                feedback_parts.append("Perfect rhythm and timing! You're really feeling the music.")
            elif scoring_result.rhythm_score >= 60:
                feedback_parts.append("Good rhythm. Try to sync your movements more closely with the beat.")
            else:
                feedback_parts.append("Focus on improving your rhythm and timing. Practice with the music more.")
            
            # Expression feedback
            if scoring_result.expression_score >= 80:
                feedback_parts.append("Amazing expression and energy! Your performance is captivating.")
            elif scoring_result.expression_score >= 60:
                feedback_parts.append("Good energy and expression. Let yourself go more and show your personality.")
            else:
                feedback_parts.append("Work on expressing yourself more. Don't be afraid to show your personality and energy.")
            
            # Difficulty feedback
            if scoring_result.difficulty_score >= 80:
                feedback_parts.append("Impressive difficulty level! You're pushing your limits.")
            elif scoring_result.difficulty_score >= 60:
                feedback_parts.append("Good challenge level. Consider trying more complex movements.")
            else:
                feedback_parts.append("Try to challenge yourself more with complex movements and combinations.")
            
            # Overall feedback
            if scoring_result.total_score >= 85:
                feedback_parts.append("Outstanding performance! You're showing great skill and artistry.")
            elif scoring_result.total_score >= 70:
                feedback_parts.append("Great job! Keep practicing and you'll continue to improve.")
            elif scoring_result.total_score >= 50:
                feedback_parts.append("Good effort! Focus on the areas mentioned above to improve.")
            else:
                feedback_parts.append("Keep practicing! Everyone starts somewhere, and you're on your way to improvement.")
            
            # Add style-specific feedback if available
            if mmpose_result.dance_style_detected:
                feedback_parts.append(f"Style detected: {mmpose_result.dance_style_detected}")
            
            return " ".join(feedback_parts)
            
        except Exception as e:
            logger.error(f"❌ Error generating feedback: {e}")
            return "Great effort! Keep practicing and improving your dance skills."
    
    def _get_fallback_analysis_data(self, submission_id: str, error_message: str) -> AnalysisData:
        """Get fallback analysis data when MMPose fails"""
        logger.warning(f"⚠️ Using fallback analysis for submission {submission_id}")
        
        return AnalysisData(
            status="failed",
            score=50,  # Default score
            breakdown={
                "technique": 50,
                "rhythm": 50,
                "expression": 50,
                "difficulty": 50
            },
            feedback=f"Analysis encountered an issue: {error_message}. Please try again or contact support.",
            pose_data_url=None,
            confidence=0.0
        )
    
    async def get_analysis_status(self, submission_id: str) -> Optional[ChallengeAnalysisResponse]:
        """Get current analysis status"""
        return await mmpose_service.get_analysis_status(submission_id)

# Global service instance
challenge_scoring_service = ChallengeScoringService() 