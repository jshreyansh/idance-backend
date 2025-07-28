from pydantic import BaseModel
from typing import Optional, List, Literal

class GeoPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [lng, lat]

class Location(BaseModel):
    city: Optional[str]
    country: Optional[str]
    geo: Optional[GeoPoint]

class UserProfileUpdate(BaseModel):
    username: Optional[str]
    displayName: Optional[str]
    avatarUrl: Optional[str]
    bio: Optional[str]
    gender: Optional[str]
    birthYear: Optional[int]
    location: Optional[Location]

class GoogleUserProfile(BaseModel):
    username: Optional[str]
    displayName: Optional[str]
    avatarUrl: Optional[str]
    gender: Optional[str]
    birthYear: Optional[int]
    phone: Optional[str]
    location: Optional[Location] 

class UserStatsUpdateRequest(BaseModel):
    kcal: int
    minutes: int
    steps: int
    stars: int
    style: str

class UserStatsResponse(BaseModel):
    totalSessions: int = 0
    totalKcal: int = 0
    totalTimeMinutes: int = 0
    totalSteps: int = 0
    currentStreakDays: int = 0
    maxStreakDays: int = 0
    lastActiveDate: Optional[str] = None
    level: int = 0
    starsEarned: int = 0
    rating: int = 0
    mostPlayedStyle: str = ""
    trophies: list = []
    weeklyActivity: Optional[List[dict]] = [] 