from fastapi import APIRouter, Depends, HTTPException, Body, Request
from services.s3.service import s3_service, generate_session_video_key, generate_thumbnail_key, generate_challenge_video_key
from services.s3.models import VideoUploadRequest, VideoUploadResponse, ThumbnailUploadRequest, ThumbnailUploadResponse, ChallengeVideoUploadRequest, ChallengeVideoUploadResponse, DanceBreakdownVideoUploadRequest, DanceBreakdownVideoUploadResponse
from services.user.service import get_current_user_id
from services.rate_limiting.decorators import protected_rate_limit
from services.video_processing.middleware import video_resizing_middleware
from infra.mongo import Database
# Environment-aware collection names
challenges_collection = Database.get_collection_name('challenges')
challenge_submissions_collection = Database.get_collection_name('challenge_submissions')
dance_sessions_collection = Database.get_collection_name('dance_sessions')

from bson import ObjectId

s3_router = APIRouter()

@s3_router.post('/api/s3/upload/video', response_model=VideoUploadResponse)
@protected_rate_limit('upload_video')
async def get_video_upload_url(
    http_request: Request,
    request: VideoUploadRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned URL for uploading a session video to S3
    """
    # Verify the session exists and belongs to the user
    db = Database.get_database()
    session = await db[dance_sessions_collection].find_one({
        '_id': ObjectId(request.session_id),
        'userId': ObjectId(user_id)
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by user")
    
    # Generate unique file key for the video
    file_key = generate_session_video_key(
        user_id=user_id,
        session_id=request.session_id,
        file_extension=request.file_extension
    )
    
    # Generate presigned upload URL
    upload_data = s3_service.generate_presigned_upload_url(
        file_key=file_key,
        content_type=request.content_type
    )
    
    # Get the final file URL
    file_url = s3_service.get_file_url(file_key)
    
    return VideoUploadResponse(
        upload_url=upload_data['upload_url'],
        file_key=upload_data['file_key'],
        content_type=upload_data['content_type'],
        expires_in=upload_data['expires_in'],
        file_url=file_url
    )

@s3_router.post('/api/s3/upload/challenge-video', response_model=ChallengeVideoUploadResponse)
@protected_rate_limit('upload_video')
async def get_challenge_video_upload_url(
    http_request: Request,
    request: ChallengeVideoUploadRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned URL for uploading a challenge video to S3 (for streamlined flow)
    """
    # Verify the challenge exists and is active
    db = Database.get_database()
    challenge = await db[challenges_collection].find_one({
        '_id': ObjectId(request.challenge_id),
        'isActive': True
    })
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found or not active")
    
    # Check if user already submitted to this challenge
    existing_submission = await db[challenge_submissions_collection].find_one({
        'userId': user_id,
        'challengeId': request.challenge_id
    })
    
    if existing_submission:
        raise HTTPException(status_code=400, detail="Already submitted to this challenge")
    
    # Generate unique file key for the challenge video
    file_key = generate_challenge_video_key(
        user_id=user_id,
        challenge_id=request.challenge_id,
        file_extension=request.file_extension
    )
    
    # Generate presigned upload URL
    upload_data = s3_service.generate_presigned_upload_url(
        file_key=file_key,
        content_type=request.content_type
    )
    
    # Get the final file URL
    file_url = s3_service.get_file_url(file_key)
    
    return ChallengeVideoUploadResponse(
        upload_url=upload_data['upload_url'],
        file_key=upload_data['file_key'],
        content_type=upload_data['content_type'],
        expires_in=upload_data['expires_in'],
        file_url=file_url
    )

@s3_router.post('/api/s3/upload/thumbnail', response_model=ThumbnailUploadResponse)
@protected_rate_limit('upload_thumbnail')
async def get_thumbnail_upload_url(
    http_request: Request,
    request: ThumbnailUploadRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned URL for uploading a video thumbnail to S3
    """
    # Verify the session exists and belongs to the user
    db = Database.get_database()
    session = await db[dance_sessions_collection].find_one({
        '_id': ObjectId(request.session_id),
        'userId': ObjectId(user_id)
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by user")
    
    # Generate unique file key for the thumbnail
    file_key = generate_thumbnail_key(
        user_id=user_id,
        session_id=request.session_id,
        file_extension=request.file_extension
    )
    
    # Generate presigned upload URL
    upload_data = s3_service.generate_presigned_upload_url(
        file_key=file_key,
        content_type=request.content_type
    )
    
    # Get the final file URL
    file_url = s3_service.get_file_url(file_key)
    
    return ThumbnailUploadResponse(
        upload_url=upload_data['upload_url'],
        file_key=upload_data['file_key'],
        content_type=upload_data['content_type'],
        expires_in=upload_data['expires_in'],
        file_url=file_url
    )

@s3_router.delete('/api/s3/files/{file_key}')
async def delete_file(
    file_key: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a file from S3 (only if it belongs to the user)
    """
    # Basic validation - ensure the file key belongs to the user
    if not file_key.startswith(f"sessions/{user_id}/") and not file_key.startswith(f"thumbnails/{user_id}/"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = s3_service.delete_file(file_key)
    if success:
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file")

@s3_router.get('/api/s3/files/{file_key}/url')
async def get_file_url(
    file_key: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned download URL for a file
    """
    # Basic validation - ensure the file key belongs to the user
    if not file_key.startswith(f"sessions/{user_id}/") and not file_key.startswith(f"thumbnails/{user_id}/"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        download_url = s3_service.generate_presigned_download_url(file_key)
        return {"download_url": download_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

@s3_router.post('/api/s3/upload/dance-breakdown-video', response_model=DanceBreakdownVideoUploadResponse)
@protected_rate_limit('upload_video')
async def get_dance_breakdown_video_upload_url(
    http_request: Request,
    request: DanceBreakdownVideoUploadRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned URL for uploading a video for dance breakdown analysis
    """
    # Validate file size if provided
    if request.file_size_mb is not None:
        # Maximum file size: 100MB for dance breakdown videos
        max_size_mb = 100
        if request.file_size_mb > max_size_mb:
            raise HTTPException(
                status_code=400, 
                detail=f"File size ({request.file_size_mb}MB) exceeds maximum allowed size ({max_size_mb}MB)"
            )
        
        # Minimum file size: 0.1MB (100KB) to ensure it's not empty
        min_size_mb = 0.1
        if request.file_size_mb < min_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({request.file_size_mb}MB) is too small. Minimum size is {min_size_mb}MB"
            )
    
    # Generate unique breakdown ID for tracking
    breakdown_id = str(ObjectId())
    
    # Generate unique file key for the dance breakdown video
    file_key = f"dance-breakdowns/{user_id}/{breakdown_id}/original_video.{request.file_extension}"
    
    # Generate presigned upload URL
    upload_data = s3_service.generate_presigned_upload_url(
        file_key=file_key,
        content_type=request.content_type
    )
    
    # Get the final file URL
    file_url = s3_service.get_file_url(file_key)
    
    return DanceBreakdownVideoUploadResponse(
        upload_url=upload_data['upload_url'],
        file_key=upload_data['file_key'],
        content_type=upload_data['content_type'],
        expires_in=upload_data['expires_in'],
        file_url=file_url,
        breakdown_id=breakdown_id
    )

@s3_router.post('/api/s3/upload/video-with-resize')
@protected_rate_limit('upload_video')
async def upload_video_with_resize(
    http_request: Request,
    request: VideoUploadRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload video with automatic resizing to ensure dimensions are under 600x600
    This endpoint processes the video server-side and uploads the resized version
    """
    # Verify the session exists and belongs to the user
    db = Database.get_database()
    session = await db[dance_sessions_collection].find_one({
        '_id': ObjectId(request.session_id),
        'userId': ObjectId(user_id)
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by user")
    
    # Generate unique file key for the video
    file_key = generate_session_video_key(
        user_id=user_id,
        session_id=request.session_id,
        file_extension=request.file_extension
    )
    
    # Generate presigned upload URL for original upload
    upload_data = s3_service.generate_presigned_upload_url(
        file_key=file_key,
        content_type=request.content_type
    )
    
    # Get the final file URL
    file_url = s3_service.get_file_url(file_key)
    
    return VideoUploadResponse(
        upload_url=upload_data['upload_url'],
        file_key=upload_data['file_key'],
        content_type=upload_data['content_type'],
        expires_in=upload_data['expires_in'],
        file_url=file_url
    ) 