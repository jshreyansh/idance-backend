#!/usr/bin/env python3
"""
AI Service Router for pose analysis and scoring endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from services.ai.models import AnalysisRequest, AnalysisResponse
from services.ai.pose_analysis import pose_analysis_service
from services.user.service import get_current_user_id
from typing import Dict
import logging

logger = logging.getLogger(__name__)

ai_router = APIRouter()

@ai_router.post('/api/ai/analyze-pose', response_model=AnalysisResponse)
async def analyze_pose(
    request: AnalysisRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Trigger pose analysis for a video submission
    """
    try:
        logger.info(f"🎬 AI analysis requested for submission {request.submission_id}")
        
        # Start pose analysis
        result = await pose_analysis_service.analyze_pose(request)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in pose analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@ai_router.get('/api/ai/analysis-status/{submission_id}', response_model=AnalysisResponse)
async def get_analysis_status(
    submission_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get current analysis status for a submission
    """
    try:
        status = await pose_analysis_service.get_analysis_status(submission_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@ai_router.post('/api/ai/score-submission', response_model=Dict)
async def score_submission(
    submission_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Manually trigger scoring for a submission
    """
    try:
        logger.info(f"🎯 Manual scoring requested for submission {submission_id}")
        
        # For now, this will trigger a new analysis
        # In the future, this will use existing pose data
        request = AnalysisRequest(
            submission_id=submission_id,
            video_url="mock_video_url",
            challenge_type="freestyle"
        )
        
        result = await pose_analysis_service.analyze_pose(request)
        
        return {
            "submission_id": submission_id,
            "status": "scored",
            "score_breakdown": result.score_breakdown.dict() if result.score_breakdown else None,
            "total_score": result.total_score,
            "feedback": result.feedback
        }
        
    except Exception as e:
        logger.error(f"❌ Error in manual scoring: {e}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")

@ai_router.get('/api/ai/health')
async def ai_health():
    """
    Health check for AI service
    """
    return {
        "status": "healthy",
        "service": "ai_pose_analysis",
        "active_analyses": len(pose_analysis_service.analysis_queue),
        "version": "1.0.0"
    } 