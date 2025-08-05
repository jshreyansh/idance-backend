from fastapi import APIRouter, HTTPException, Depends
from services.ai.models import AnalysisRequest, AnalysisResponse, DanceBreakdownRequest, DanceBreakdownResponse
from services.ai.pose_analysis import pose_analysis_service
from services.ai.dance_breakdown import dance_breakdown_service
from services.user.service import get_current_user_id
from typing import Dict
import logging

logger = logging.getLogger(__name__)

ai_router = APIRouter()

@ai_router.get('/ai/health')
def ai_health():
    return {"status": "ai service ok"}

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
    request: dict,
    user_id: str = Depends(get_current_user_id)
):
    submission_id = request.get("submission_id")
    if not submission_id:
        raise HTTPException(status_code=400, detail="submission_id is required")
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

@ai_router.get('/api/ai/dance-breakdown/{breakdown_id}')
async def get_dance_breakdown(
    breakdown_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get specific dance breakdown by ID
    """
    try:
        logger.info(f"📋 Getting breakdown {breakdown_id} for user {user_id}")
        
        breakdown = await dance_breakdown_service.get_breakdown_by_id(breakdown_id, user_id)
        
        if not breakdown:
            raise HTTPException(status_code=404, detail="Dance breakdown not found or not owned by user")
        
        return breakdown
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting dance breakdown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get breakdown: {str(e)}")

@ai_router.get('/api/ai/dance-breakdowns')
async def get_user_dance_breakdowns(
    limit: int = 20,
    skip: int = 0,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get user's dance breakdown history
    """
    try:
        logger.info(f"📊 Getting breakdown history for user {user_id} (limit: {limit}, skip: {skip})")
        
        breakdowns = await dance_breakdown_service.get_user_breakdowns(user_id, limit, skip)
        
        return {
            "success": True,
            "total": len(breakdowns),
            "breakdowns": breakdowns,
            "pagination": {
                "limit": limit,
                "skip": skip,
                "has_more": len(breakdowns) == limit
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting user breakdowns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get breakdowns: {str(e)}") 