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