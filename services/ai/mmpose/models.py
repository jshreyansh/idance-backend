#!/usr/bin/env python3
"""
MMPose-specific models for dance analysis
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np

class MMPoseKeypoint(BaseModel):
    """Enhanced keypoint with MMPose-specific data"""
    x: float
    y: float
    z: Optional[float] = None  # 3D position if available
    confidence: float
    keypoint_type: str
    visibility: float = 1.0
    track_id: Optional[int] = None  # For multi-person tracking

class MMPoseFrame(BaseModel):
    """Enhanced frame data with MMPose features"""
    frame_number: int
    timestamp: float
    keypoints: List[MMPoseKeypoint]
    frame_confidence: float
    person_id: Optional[int] = None  # For multi-person scenarios
    bbox: Optional[List[float]] = None  # Bounding box [x1, y1, x2, y2]
    pose_score: float = 0.0

class DanceTechniqueMetrics(BaseModel):
    """Dance-specific technique analysis"""
    balance_stability: float = Field(..., ge=0.0, le=1.0, description="Balance stability score")
    joint_alignment: float = Field(..., ge=0.0, le=1.0, description="Joint alignment accuracy")
    posture_quality: float = Field(..., ge=0.0, le=1.0, description="Overall posture quality")
    movement_precision: float = Field(..., ge=0.0, le=1.0, description="Movement precision")
    technique_consistency: float = Field(..., ge=0.0, le=1.0, description="Technique consistency")

class RhythmMetrics(BaseModel):
    """Rhythm and timing analysis"""
    beat_synchronization: float = Field(..., ge=0.0, le=1.0, description="Beat synchronization")
    movement_timing: float = Field(..., ge=0.0, le=1.0, description="Movement timing accuracy")
    rhythm_consistency: float = Field(..., ge=0.0, le=1.0, description="Rhythm consistency")
    tempo_matching: float = Field(..., ge=0.0, le=1.0, description="Tempo matching")
    musicality: float = Field(..., ge=0.0, le=1.0, description="Overall musicality")

class ExpressionMetrics(BaseModel):
    """Movement expression and quality"""
    movement_flow: float = Field(..., ge=0.0, le=1.0, description="Movement flow and fluidity")
    energy_expression: float = Field(..., ge=0.0, le=1.0, description="Energy expression")
    style_authenticity: float = Field(..., ge=0.0, le=1.0, description="Style authenticity")
    performance_quality: float = Field(..., ge=0.0, le=1.0, description="Overall performance quality")
    artistic_expression: float = Field(..., ge=0.0, le=1.0, description="Artistic expression")

class DifficultyMetrics(BaseModel):
    """Movement difficulty assessment"""
    movement_complexity: float = Field(..., ge=0.0, le=1.0, description="Movement complexity")
    physical_demand: float = Field(..., ge=0.0, le=1.0, description="Physical demand")
    skill_requirement: float = Field(..., ge=0.0, le=1.0, description="Skill requirement")
    coordination_difficulty: float = Field(..., ge=0.0, le=1.0, description="Coordination difficulty")
    overall_difficulty: float = Field(..., ge=0.0, le=1.0, description="Overall difficulty")

class DanceScoringResult(BaseModel):
    """Comprehensive dance scoring result"""
    technique: DanceTechniqueMetrics
    rhythm: RhythmMetrics
    expression: ExpressionMetrics
    difficulty: DifficultyMetrics
    
    # Overall scores (0-100)
    technique_score: int = Field(..., ge=0, le=100)
    rhythm_score: int = Field(..., ge=0, le=100)
    expression_score: int = Field(..., ge=0, le=100)
    difficulty_score: int = Field(..., ge=0, le=100)
    total_score: int = Field(..., ge=0, le=100)
    
    # Analysis metadata
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time: float
    frames_analyzed: int
    total_frames: int
    
    @property
    def accuracy_percentage(self) -> float:
        """Calculate analysis accuracy percentage"""
        return (self.frames_analyzed / self.total_frames) * 100 if self.total_frames > 0 else 0.0

class ReferenceComparisonResult(BaseModel):
    """Result of comparing against reference video"""
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    technique_similarity: float = Field(..., ge=0.0, le=1.0)
    timing_similarity: float = Field(..., ge=0.0, le=1.0)
    movement_similarity: float = Field(..., ge=0.0, le=1.0)
    differences: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

class MMPoseAnalysisResult(BaseModel):
    """Complete MMPose analysis result"""
    submission_id: str
    video_url: str
    challenge_type: str
    
    # Pose data
    pose_frames: List[MMPoseFrame]
    total_frames: int
    frames_analyzed: int
    analysis_confidence: float
    
    # Scoring results
    scoring_result: DanceScoringResult
    
    # Reference comparison (if available)
    reference_comparison: Optional[ReferenceComparisonResult] = None
    
    # Metadata
    processing_time: float
    model_version: str = "mmpose-1.1.0"
    created_at: datetime
    
    # Analysis details
    dance_style_detected: Optional[str] = None
    skill_level_assessed: Optional[str] = None
    key_movements_identified: List[str] = Field(default_factory=list)
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if analysis has high confidence"""
        return self.analysis_confidence >= 0.8 and self.scoring_result.confidence >= 0.8

class DanceStyleClassification(BaseModel):
    """Dance style classification result"""
    primary_style: str
    confidence: float
    secondary_styles: List[Dict[str, float]] = Field(default_factory=list)
    style_indicators: List[str] = Field(default_factory=list)

class MovementAnalysis(BaseModel):
    """Detailed movement analysis"""
    movement_phases: List[Dict[str, Any]] = Field(default_factory=list)
    key_transitions: List[Dict[str, Any]] = Field(default_factory=list)
    movement_patterns: List[str] = Field(default_factory=list)
    energy_distribution: Dict[str, float] = Field(default_factory=dict)
    spatial_usage: Dict[str, float] = Field(default_factory=dict)

class ChallengeAnalysisRequest(BaseModel):
    """Request for challenge analysis"""
    submission_id: str
    video_url: str
    challenge_type: str
    challenge_difficulty: str
    reference_video_url: Optional[str] = None
    target_bpm: Optional[int] = None
    dance_style: Optional[str] = None

class ChallengeAnalysisResponse(BaseModel):
    """Response for challenge analysis"""
    submission_id: str
    status: str  # "processing", "completed", "failed"
    progress: float = 0.0
    
    # Results (only available when completed)
    analysis_result: Optional[MMPoseAnalysisResult] = None
    
    # Error information (only available when failed)
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    # Metadata
    created_at: datetime
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None 