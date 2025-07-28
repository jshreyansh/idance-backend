from pydantic import BaseModel, Field
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
    demoVideoFileKey: str = Field(..., description="S3 file key for demo video")
    points: int = Field(..., ge=1, le=1000)
    badgeName: str = Field(..., min_length=1, max_length=50)
    badgeIconURL: str = Field(..., description="URL for badge icon")
    scoringCriteria: Optional[ChallengeCriteria] = None
    thumbnailURL: Optional[str] = None

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
    isActive: bool = True
    createdBy: str
    createdAt: datetime
    updatedAt: datetime
    
    # Analytics
    totalSubmissions: int = 0
    averageScore: float = 0.0
    topScore: int = 0

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
    isActive: bool = True
    createdBy: str
    createdAt: datetime
    updatedAt: datetime
    
    # Analytics
    totalSubmissions: int = 0
    averageScore: float = 0.0
    topScore: int = 0

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