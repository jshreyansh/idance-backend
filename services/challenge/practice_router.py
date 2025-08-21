#!/usr/bin/env python3
"""
Practice Scoring Router for Challenge Attempts
Provides endpoints for scoring practice attempts without saving videos
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from services.challenge.practice_scoring import practice_scoring_service
from services.user.service import get_current_user_id
from services.rate_limiting.decorators import protected_rate_limit
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

practice_router = APIRouter()

@practice_router.post('/api/challenges/{challenge_id}/practice-score')
@protected_rate_limit('practice_scoring')
async def score_practice_attempt(
    challenge_id: str,
    practice_video: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Score a practice attempt for a challenge
    
    This endpoint analyzes a practice video against the challenge reference
    and returns a detailed score breakdown with improvement suggestions.
    The practice video is NOT saved - only analyzed temporarily.
    
    Args:
        challenge_id: ID of the challenge being practiced
        practice_video: Video file of the practice attempt
        user_id: ID of the user (from authentication)
        
    Returns:
        Detailed score breakdown with feedback and suggestions
    """
    try:
        # Validate file type
        if not practice_video.content_type.startswith('video/'):
            raise HTTPException(
                status_code=400, 
                detail="File must be a video (mp4, mov, avi, etc.)"
            )
        
        # Validate file size (max 100MB for practice)
        content = await practice_video.read()
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > 100:
            raise HTTPException(
                status_code=400,
                detail="Practice video file size must be under 100MB"
            )
        
        # Reset file pointer for processing
        await practice_video.seek(0)
        
        # Score the practice attempt
        score_result = await practice_scoring_service.score_practice_attempt(
            practice_video=practice_video,
            challenge_id=challenge_id,
            user_id=user_id
        )
        
        logger.info(f"✅ Practice scoring completed for user {user_id} on challenge {challenge_id}")
        return score_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in practice scoring endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Practice scoring failed")

@practice_router.get('/api/challenges/{challenge_id}/practice-info')
@protected_rate_limit('practice_info')
async def get_practice_info(
    challenge_id: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Get information about practice scoring for a challenge
    
    Returns details about the challenge and practice scoring capabilities.
    
    Args:
        challenge_id: ID of the challenge
        user_id: ID of the user (from authentication)
        
    Returns:
        Challenge practice information
    """
    try:
        from infra.mongo import Database
        from bson import ObjectId
        
        db = Database.get_database()
        challenges_collection = Database.get_collection_name('challenges')
        
        # Get challenge details
        challenge = await db[challenges_collection].find_one({'_id': ObjectId(challenge_id)})
        
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Check if user has already submitted to this challenge
        challenge_submissions_collection = Database.get_collection_name('challenge_submissions')
        existing_submission = await db[challenge_submissions_collection].find_one({
            'userId': user_id,
            'challengeId': challenge_id
        })
        
        practice_info = {
            "challenge_id": challenge_id,
            "challenge_title": challenge.get('title', 'Unknown Challenge'),
            "challenge_description": challenge.get('description', ''),
            "has_reference_video": 'demoVideoFileKey' in challenge and challenge['demoVideoFileKey'],
            "practice_scoring_available": True,
            "max_practice_video_size_mb": 100,
            "supported_video_formats": ["mp4", "mov", "avi", "mkv", "webm"],
            "scoring_categories": [
                "technique",
                "rhythm", 
                "expression",
                "difficulty"
            ],
            "user_has_submitted": existing_submission is not None,
            "practice_tips": [
                "Record your practice attempts to track improvement",
                "Focus on one scoring category at a time",
                "Compare your practice scores to identify areas for improvement",
                "Practice multiple times before final submission"
            ]
        }
        
        return practice_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting practice info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get practice information")

@practice_router.get('/api/challenges/{challenge_id}/practice-history')
@protected_rate_limit('practice_history')
async def get_practice_history(
    challenge_id: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Get practice history for a user on a specific challenge
    
    Note: Since practice attempts are not saved, this returns a message
    indicating that practice history is not stored for privacy.
    
    Args:
        challenge_id: ID of the challenge
        user_id: ID of the user (from authentication)
        
    Returns:
        Practice history information
    """
    return {
        "challenge_id": challenge_id,
        "user_id": user_id,
        "message": "Practice attempts are not stored for privacy. Each practice session provides immediate feedback for improvement.",
        "practice_history_available": False,
        "privacy_note": "Practice videos are analyzed temporarily and not saved to protect user privacy",
        "recommendation": "Take notes of your scores and improvement areas during practice sessions"
    } 