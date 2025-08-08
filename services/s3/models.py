from pydantic import BaseModel
from typing import Optional

class VideoUploadRequest(BaseModel):
    session_id: str
    file_extension: str = "mp4"
    content_type: str = "video/mp4"
    file_size_mb: Optional[float] = None

class VideoUploadResponse(BaseModel):
    upload_url: str
    file_key: str
    content_type: str
    expires_in: int
    file_url: str

class ChallengeVideoUploadRequest(BaseModel):
    challenge_id: str
    file_extension: str = "mp4"
    content_type: str = "video/mp4"
    file_size_mb: Optional[float] = None

class ChallengeVideoUploadResponse(BaseModel):
    upload_url: str
    file_key: str
    content_type: str
    expires_in: int
    file_url: str

class ThumbnailUploadRequest(BaseModel):
    session_id: str
    file_extension: str = "jpg"
    content_type: str = "image/jpeg"

class ThumbnailUploadResponse(BaseModel):
    upload_url: str
    file_key: str
    content_type: str
    expires_in: int
    file_url: str

# Dance Breakdown Video Upload Models
class DanceBreakdownVideoUploadRequest(BaseModel):
    file_extension: str = "mp4"
    content_type: str = "video/mp4"
    file_size_mb: Optional[float] = None
    original_filename: Optional[str] = None

class DanceBreakdownVideoUploadResponse(BaseModel):
    upload_url: str
    file_key: str
    content_type: str
    expires_in: int
    file_url: str
    breakdown_id: str  # Generated breakdown ID for tracking 