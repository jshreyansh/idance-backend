from fastapi import APIRouter, Depends, HTTPException, Body
from services.s3.service import s3_service, generate_session_video_key, generate_thumbnail_key, generate_challenge_video_key
from services.s3.models import VideoUploadRequest, VideoUploadResponse, ThumbnailUploadRequest, ThumbnailUploadResponse, ChallengeVideoUploadRequest, ChallengeVideoUploadResponse
from services.user.service import get_current_user_id
from infra.mongo import Database
from bson import ObjectId

s3_router = APIRouter()

@s3_router.post('/api/s3/upload/video', response_model=VideoUploadResponse)
async def get_video_upload_url(
    request: VideoUploadRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned URL for uploading a session video to S3
    """
    # Verify the session exists and belongs to the user
    db = Database.get_database()
    session = await db['dance_sessions'].find_one({
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
async def get_challenge_video_upload_url(
    request: ChallengeVideoUploadRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned URL for uploading a challenge video to S3 (for streamlined flow)
    """
    # Verify the challenge exists and is active
    db = Database.get_database()
    challenge = await db['challenges'].find_one({
        '_id': ObjectId(request.challenge_id),
        'isActive': True
    })
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found or not active")
    
    # Check if user already submitted to this challenge
    existing_submission = await db['challenge_submissions'].find_one({
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
async def get_thumbnail_upload_url(
    request: ThumbnailUploadRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned URL for uploading a video thumbnail to S3
    """
    # Verify the session exists and belongs to the user
    db = Database.get_database()
    session = await db['dance_sessions'].find_one({
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