#!/usr/bin/env python3
"""
AI Service Router for pose analysis and scoring endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from services.ai.models import AnalysisRequest, AnalysisResponse, DanceBreakdownRequest, DanceBreakdownResponse
from services.ai.enhanced_scoring import enhanced_scoring_service
from services.ai.dance_breakdown import dance_breakdown_service
from services.user.service import get_current_user_id
from typing import Dict
from datetime import datetime
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
        
        # Start enhanced scoring analysis
        result = await enhanced_scoring_service.analyze_challenge_submission(
            submission_id=request.submission_id,
            video_url=request.video_url,
            challenge_type=request.challenge_type,
            challenge_difficulty="beginner",  # Default difficulty
            target_bpm=request.target_bpm
        )
        
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
        # Enhanced scoring doesn't have status tracking, return completed status
        status = AnalysisResponse(
            submission_id=submission_id,
            status="completed",
            progress=1.0,
            created_at=datetime.utcnow()
        )
        
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
        
        result = await enhanced_scoring_service.analyze_challenge_submission(
            submission_id=submission_id,
            video_url="mock_video_url",
            challenge_type="freestyle",
            challenge_difficulty="beginner",
            target_bpm=None
        )
        
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

# ===== DANCE BREAKDOWN ENDPOINTS =====

@ai_router.post('/api/ai/dance-breakdown', response_model=DanceBreakdownResponse)
async def create_dance_breakdown(
    request: DanceBreakdownRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create step-by-step dance breakdown from YouTube/Instagram URL
    """
    try:
        logger.info(f"🎬 Dance breakdown requested for URL: {request.video_url}")
        logger.info(f"🎬 Mode: {request.mode}")
        
        # Process dance breakdown
        result = await dance_breakdown_service.process_dance_breakdown(request, user_id)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message or "Dance breakdown failed")
        
        logger.info(f"✅ Dance breakdown completed successfully")
        logger.info(f"📊 Generated {len(result.steps)} steps")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in dance breakdown endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Dance breakdown failed: {str(e)}")

@ai_router.get('/api/ai/dance-breakdown/{breakdown_id}', response_model=DanceBreakdownResponse)
async def get_dance_breakdown(
    breakdown_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get dance breakdown by ID (for future caching implementation)
    """
    try:
        # For now, return a mock response
        # In the future, this will retrieve from database/cache
        raise HTTPException(status_code=404, detail="Dance breakdown not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting dance breakdown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get breakdown: {str(e)}")

@ai_router.get('/api/ai/dance-breakdowns/videos')
async def get_breakdown_videos(
    page: int = 1,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all breakdown videos for the input screen
    Shows recent breakdowns by people with video URLs and thumbnails
    """
    try:
        result = await dance_breakdown_service.get_all_breakdown_videos(page, limit)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in get breakdown videos endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get breakdown videos: {str(e)}")

@ai_router.get('/api/ai/health')
async def ai_health():
    """
    Health check for AI service
    """
    return {
        "status": "healthy",
        "service": "ai_pose_analysis",
        "active_analyses": 0,  # Enhanced scoring doesn't use queue
        "version": "1.0.0",
        "features": [
            "pose_analysis",
            "dance_breakdown"
        ]
    }

# ===== CACHE MANAGEMENT ENDPOINTS =====

@ai_router.get('/api/ai/dance-breakdowns/statistics')
async def get_breakdown_statistics(
    user_id: str = Depends(get_current_user_id)
):
    """
    Get statistics about dance breakdowns including cache effectiveness
    """
    try:
        stats = await dance_breakdown_service.get_breakdown_statistics()
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting breakdown statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@ai_router.post('/api/ai/dance-breakdowns/clear-duplicates')
async def clear_duplicate_breakdowns(
    user_id: str = Depends(get_current_user_id)
):
    """
    Remove duplicate breakdowns for the same video URL, keeping only the most recent successful one
    """
    try:
        result = await dance_breakdown_service.clear_duplicate_breakdowns()
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Error clearing duplicate breakdowns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear duplicates: {str(e)}")

@ai_router.get('/api/ai/dance-breakdowns/cache-status/{video_url:path}')
async def check_cache_status(
    video_url: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Check if a video URL has an existing breakdown in cache
    """
    try:
        # URL decode the video URL
        import urllib.parse
        decoded_url = urllib.parse.unquote(video_url)
        
        existing_breakdown = await dance_breakdown_service.get_breakdown_by_video_url(decoded_url)
        
        return {
            "success": True,
            "video_url": decoded_url,
            "cached": existing_breakdown is not None,
            "breakdown_id": str(existing_breakdown["_id"]) if existing_breakdown else None,
            "created_at": existing_breakdown.get("createdAt") if existing_breakdown else None
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check cache status: {str(e)}") 