#!/usr/bin/env python3
"""
AI Service Models for pose analysis and scoring
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class PoseKeypoint(BaseModel):
    """Individual pose keypoint data"""
    x: float
    y: float
    confidence: float
    keypoint_type: str  # e.g., "nose", "left_shoulder", etc.

class PoseFrame(BaseModel):
    """Pose data for a single video frame"""
    frame_number: int
    timestamp: float
    keypoints: List[PoseKeypoint]
    frame_confidence: float

class PoseAnalysisResult(BaseModel):
    """Complete pose analysis result"""
    submission_id: str
    total_frames: int
    frames_analyzed: int
    pose_frames: List[PoseFrame]
    analysis_confidence: float
    processing_time: float
    created_at: datetime

class ScoreBreakdown(BaseModel):
    """Detailed scoring breakdown"""
    balance: int = Field(..., ge=0, le=25, description="Balance hold score (0-25)")
    rhythm: int = Field(..., ge=0, le=30, description="Rhythm/tempo score (0-30)")
    smoothness: int = Field(..., ge=0, le=25, description="Movement smoothness (0-25)")
    creativity: int = Field(..., ge=0, le=20, description="Freestyle creativity (0-20)")
    
    @property
    def total_score(self) -> int:
        """Calculate total score from breakdown"""
        return self.balance + self.rhythm + self.smoothness + self.creativity

class AnalysisRequest(BaseModel):
    """Request for pose analysis"""
    submission_id: str
    video_url: str
    challenge_type: str = "freestyle"
    target_bpm: Optional[int] = None

class AnalysisResponse(BaseModel):
    """Response from pose analysis"""
    submission_id: str
    status: str  # "processing", "completed", "failed"
    progress: float = 0.0  # 0.0 to 1.0
    pose_data_url: Optional[str] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    total_score: Optional[int] = None
    feedback: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class FeedbackComponent(BaseModel):
    """Individual feedback component"""
    category: str  # "balance", "rhythm", "smoothness", "creativity"
    score: int
    message: str
    suggestions: List[str]

class CompleteFeedback(BaseModel):
    """Complete feedback for a submission"""
    submission_id: str
    total_score: int
    score_breakdown: ScoreBreakdown
    components: List[FeedbackComponent]
    overall_message: str
    improvement_suggestions: List[str]
    generated_at: datetime 