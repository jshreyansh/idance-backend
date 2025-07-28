from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SessionStartRequest(BaseModel):
    style: str
    sessionType: str
    isPublic: bool = True
    sharedToFeed: bool = False
    remixable: bool = False
    promptUsed: Optional[str] = None
    inspirationSessionId: Optional[str] = None
    location: Optional[str] = None
    highlightText: Optional[str] = None
    tags: Optional[List[str]] = None

class SessionCompleteRequest(BaseModel):
    sessionId: str
    endTime: datetime
    durationMinutes: int
    caloriesBurned: int
    videoURL: Optional[str] = None
    videoFileKey: Optional[str] = None  # S3 file key for the video
    thumbnailURL: Optional[str] = None  # Thumbnail URL
    thumbnailFileKey: Optional[str] = None  # S3 file key for the thumbnail
    score: Optional[int] = None
    stars: Optional[int] = None
    rating: Optional[int] = None
    highlightText: Optional[str] = None
    tags: Optional[List[str]] = None

class SessionResponse(BaseModel):
    id: str = Field(..., alias="_id")
    userId: str
    startTime: datetime
    endTime: Optional[datetime] = None
    status: str
    durationMinutes: Optional[int] = None
    caloriesBurned: Optional[int] = None
    style: str
    sessionType: str
    videoURL: Optional[str] = None
    videoFileKey: Optional[str] = None
    thumbnailURL: Optional[str] = None
    thumbnailFileKey: Optional[str] = None
    location: Optional[str] = None
    highlightText: Optional[str] = None
    tags: Optional[List[str]] = None
    score: Optional[int] = None
    stars: Optional[int] = None
    rating: Optional[int] = None
    isPublic: bool
    sharedToFeed: bool
    remixable: bool
    promptUsed: Optional[str] = None
    inspirationSessionId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime 