#!/usr/bin/env python3
"""
Background job router for manual triggers and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends
from services.background.jobs import background_job_service
from services.user.service import get_current_user_id
from typing import Dict

background_router = APIRouter()

@background_router.post('/api/admin/jobs/rotate-challenges')
async def trigger_challenge_rotation(user_id: str = Depends(get_current_user_id)) -> Dict:
    """
    Manually trigger challenge rotation (admin only)
    """
    # TODO: Add admin role check
    result = await background_job_service.rotate_daily_challenges()
    
    if result["success"]:
        return {
            "message": "Challenge rotation completed successfully",
            "details": result
        }
    else:
        raise HTTPException(status_code=500, detail=f"Challenge rotation failed: {result['error']}")

@background_router.post('/api/admin/jobs/cleanup')
async def trigger_data_cleanup(user_id: str = Depends(get_current_user_id)) -> Dict:
    """
    Manually trigger data cleanup (admin only)
    """
    # TODO: Add admin role check
    result = await background_job_service.cleanup_old_data()
    
    if result["success"]:
        return {
            "message": "Data cleanup completed successfully",
            "details": result
        }
    else:
        raise HTTPException(status_code=500, detail=f"Data cleanup failed: {result['error']}")

@background_router.get('/api/admin/jobs/status')
async def get_job_status(user_id: str = Depends(get_current_user_id)) -> Dict:
    """
    Get background job status and statistics (admin only)
    """
    # TODO: Add admin role check
    return {
        "status": "Background jobs are running",
        "available_jobs": [
            "rotate_daily_challenges",
            "cleanup_old_data"
        ],
        "last_run": "2025-01-28T10:00:00Z",  # TODO: Implement actual tracking
        "next_scheduled": "2025-01-29T00:00:00Z"  # TODO: Implement actual scheduling
    } 