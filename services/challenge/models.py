from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, List, Literal, Dict
from datetime import datetime

class ChallengeCriteria(BaseModel):
    """Scoring criteria weights for different challenge types"""
    balance: int = 25      # Balance hold score weight
    rhythm: int = 30       # Tempo/rhythm matching weight  
    smoothness: int = 25   # Movement fluidity weight
    creativity: int = 20   # Freestyle creativity weight

class ChallengeCreate(BaseModel):
    """Request model for creating a new challenge"""
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    type: Literal['freestyle', 'static', 'spin', 'combo']
    difficulty: Literal['beginner', 'intermediate', 'advanced'] = 'beginner'
    startTime: datetime
    endTime: datetime
    demoVideoURL: Optional[str] = Field(None, description="Direct URL for demo video")
    demoVideoFileKey: Optional[str] = Field(None, description="S3 file key for demo video")
    points: int = Field(..., ge=1, le=1000)
    badgeName: str = Field(..., min_length=1, max_length=50)
    badgeIconURL: str = Field(..., description="URL for badge icon")
    scoringCriteria: Optional[ChallengeCriteria] = None
    thumbnailURL: Optional[str] = None
    category: Optional[str] = Field(None, description="Challenge category")
    tags: Optional[List[str]] = Field(None, description="Challenge tags")
    
    @model_validator(mode='after')
    def validate_video_source(self):
        """Ensure at least one video source is provided"""
        if not self.demoVideoURL and not self.demoVideoFileKey:
            raise ValueError('Either demoVideoURL or demoVideoFileKey must be provided')
        return self

class ChallengeResponse(BaseModel):
    """Response model for challenge data"""
    id: str = Field(..., alias="_id")
    title: str
    description: str
    type: Literal['freestyle', 'static', 'spin', 'combo']
    difficulty: Literal['beginner', 'intermediate', 'advanced']
    startTime: datetime
    endTime: datetime
    demoVideoURL: str
    demoVideoFileKey: str
    thumbnailURL: Optional[str]
    points: int
    badgeName: str
    badgeIconURL: str
    scoringCriteria: ChallengeCriteria
    category: Optional[str]
    tags: Optional[List[str]]
    isActive: bool = True
    createdBy: str
    createdAt: datetime
    updatedAt: datetime
    
    # Analytics
    totalSubmissions: int = 0
    averageScore: float = 0.0
    topScore: int = 0
    participantCount: int = 0

class Challenge(BaseModel):
    """Internal challenge model for database operations"""
    id: str = Field(..., alias="_id")
    title: str
    description: str
    type: Literal['freestyle', 'static', 'spin', 'combo']
    difficulty: Literal['beginner', 'intermediate', 'advanced']
    startTime: datetime
    endTime: datetime
    demoVideoURL: str
    demoVideoFileKey: str
    thumbnailURL: Optional[str]
    points: int
    badgeName: str
    badgeIconURL: str
    scoringCriteria: ChallengeCriteria
    category: Optional[str]
    tags: Optional[List[str]]
    isActive: bool = True
    createdBy: str
    createdAt: datetime
    updatedAt: datetime
    
    # Analytics
    totalSubmissions: int = 0
    averageScore: float = 0.0
    topScore: int = 0
    participantCount: int = 0

class ChallengeListResponse(BaseModel):
    """Response model for listing challenges"""
    challenges: List[ChallengeResponse]
    total: int
    page: int
    limit: int

class TodayChallengeResponse(BaseModel):
    """Response model for today's active challenge"""
    id: str
    title: str
    type: Literal['freestyle', 'static', 'spin', 'combo']
    timeRemaining: str  # Format: "HH:MM:SS"
    demoVideoURL: str
    points: int
    participantCount: int
    description: str
    difficulty: Literal['beginner', 'intermediate', 'advanced']
    badgeName: str
    badgeIconURL: str
    category: Optional[str]
    tags: Optional[List[str]]

# New unified submission models
class VideoData(BaseModel):
    """Video information for submissions"""
    url: str
    file_key: str
    duration: Optional[int] = None  # seconds
    size_mb: Optional[float] = None

class AnalysisData(BaseModel):
    """Analysis results for submissions"""
    status: str = "pending"  # pending, processing, completed, failed
    score: Optional[int] = None
    breakdown: Optional[Dict[str, int]] = None
    feedback: Optional[str] = None
    pose_data_url: Optional[str] = None
    confidence: Optional[float] = None

class SubmissionMetadata(BaseModel):
    """Metadata for submissions"""
    caption: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(None)
    location: Optional[str] = Field(None)
    isPublic: bool = True
    sharedToFeed: bool = True
    highlightText: Optional[str] = Field(None, max_length=200)

class UnifiedSubmissionRequest(BaseModel):
    """Unified request model for challenge submissions"""
    video_file: str = Field(..., description="Base64 encoded video or file upload")
    metadata: SubmissionMetadata

class UnifiedSubmissionResponse(BaseModel):
    """Unified response model for submissions"""
    id: str = Field(..., alias="_id")
    challengeId: str
    userId: str
    video: VideoData
    analysis: AnalysisData
    metadata: SubmissionMetadata
    userProfile: Dict
    timestamps: Dict[str, Optional[datetime]]
    likes: List[str] = []
    comments: List[Dict] = []
    shares: int = 0

class ChallengeSearchRequest(BaseModel):
    """Request model for challenge search"""
    query: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    active_only: bool = True
    page: int = 1
    limit: int = 20

class ChallengeLeaderboardEntry(BaseModel):
    """Leaderboard entry model"""
    rank: int
    userId: str
    userProfile: Dict
    score: int
    scoreBreakdown: Dict[str, int]
    submittedAt: datetime
    submissionId: str

class ChallengeLeaderboardResponse(BaseModel):
    """Response model for challenge leaderboard"""
    challengeId: str
    challengeTitle: str
    entries: List[ChallengeLeaderboardEntry]
    total: int
    userRank: Optional[int] = None 