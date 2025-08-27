from fastapi import APIRouter, Depends, HTTPException, Body, Path
from services.session.models import SessionStartRequest, SessionCompleteRequest, SessionResponse, SessionUpdateRequest
from infra.mongo import Database
from datetime import datetime, timedelta
from bson import ObjectId
from services.user.service import get_current_user_id
from services.video_processing.service import video_processing_service
from services.video_processing.background_service import background_video_processor
import logging

logger = logging.getLogger(__name__)

# Environment-aware collection names
users_collection = Database.get_collection_name('users')
dance_sessions_collection = Database.get_collection_name('dance_sessions')
user_stats_collection = Database.get_collection_name('user_stats')
session_likes_collection = Database.get_collection_name('session_likes')

session_router = APIRouter()

@session_router.get('/session/health')
def session_health():
    return {"status": "session service ok"}

@session_router.post('/api/sessions/start')
async def start_session(
    data: SessionStartRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    db = Database.get_database()
    now = datetime.utcnow()
    today = now.strftime('%Y-%m-%d')
    
    # Fetch user info for denormalization
    user = await db[users_collection].find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    profile = user.get('profile') or {}
    location_data = profile.get('location') or {}
    userProfile = {
        'displayName': profile.get('displayName', ''),
        'avatarUrl': profile.get('avatarUrl', ''),
        'isPro': user.get('isPro', False),
        'location': location_data.get('city', '')
    }
    
    # Check if user already had a session today
    existing_session_today = await db[dance_sessions_collection].find_one({
        "userId": ObjectId(user_id),
        "startTime": {
            "$gte": datetime.strptime(today, '%Y-%m-%d'),
            "$lt": datetime.strptime(today, '%Y-%m-%d') + timedelta(days=1)
        }
    })
    
    # Update streaks and daily activity if this is first session of the day
    if not existing_session_today:
        await update_user_streaks_and_activity(db, user_id, today)
    
    session_doc = {
        "userId": ObjectId(user_id),
        "userProfile": userProfile,
        "startTime": now,
        "status": "ongoing",
        "style": data.style,
        "sessionType": data.sessionType,
        "isPublic": data.isPublic,
        "sharedToFeed": data.sharedToFeed,
        "remixable": data.remixable,
        "promptUsed": data.promptUsed,
        "inspirationSessionId": ObjectId(data.inspirationSessionId) if data.inspirationSessionId else None,
        "location": data.location,
        "highlightText": data.highlightText,
        "tags": data.tags or [],
        "videoThumbnailUrl": "",  # Placeholder
        "videoDuration": 0,        # Placeholder
        "likesCount": 0,
        "commentsCount": 0,
        "createdAt": now,
        "updatedAt": now
    }
    # Remove None fields
    session_doc = {k: v for k, v in session_doc.items() if v is not None}
    result = await db[dance_sessions_collection].insert_one(session_doc)
    return {"sessionId": str(result.inserted_id)}

@session_router.put('/api/sessions/{session_id}/update')
async def update_session(
    session_id: str = Path(..., description="Session ID to update"),
    data: SessionUpdateRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update session metadata (Instagram-like editing).
    Allows updates to description and metadata even after completion.
    Video-related fields cannot be updated after completion.
    """
    db = Database.get_database()
    now = datetime.utcnow()
    
    # First, verify the session exists and belongs to the user
    session = await db[dance_sessions_collection].find_one({
        "_id": ObjectId(session_id),
        "userId": ObjectId(user_id)
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    # Check if session is completed to determine update restrictions
    is_completed = session.get("status") == "completed"
    
    # Prepare update fields from request data
    update_fields = {}
    
    # Handle inspirationSessionId conversion to ObjectId
    if data.inspirationSessionId is not None:
        try:
            update_fields["inspirationSessionId"] = ObjectId(data.inspirationSessionId)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid inspirationSessionId format")
    
    # Define fields that can be updated after completion (Instagram-like)
    editable_after_completion = [
        "highlightText", "tags", "location", "isPublic", "sharedToFeed", "remixable"
    ]
    
    # Define fields that can only be updated before completion
    pre_completion_only = [
        "style", "sessionType", "promptUsed", "inspirationSessionId"
    ]
    
    # Add fields that can be updated anytime
    for field in editable_after_completion:
        if getattr(data, field) is not None:
            update_fields[field] = getattr(data, field)
    
    # Add fields that can only be updated before completion
    if not is_completed:
        for field in pre_completion_only:
            if getattr(data, field) is not None:
                update_fields[field] = getattr(data, field)
    else:
        # Check if user is trying to update pre-completion fields
        restricted_fields = []
        for field in pre_completion_only:
            if getattr(data, field) is not None:
                restricted_fields.append(field)
        
        if restricted_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot update these fields after completion: {', '.join(restricted_fields)}"
            )
    
    # Add updatedAt timestamp
    update_fields["updatedAt"] = now
    
    # Only update if there are fields to update
    if not update_fields:
        return {"message": "No fields to update"}
    
    # Perform the update
    result = await db[dance_sessions_collection].update_one(
        {"_id": ObjectId(session_id), "userId": ObjectId(user_id)},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    if result.modified_count == 0:
        return {"message": "Session updated (no changes made)"}
    
    logger.info(f"✅ Session {session_id} updated successfully by user {user_id}")
    return {"message": "Session updated successfully"}

async def update_user_streaks_and_activity(db, user_id, today):
    user_stats = await db[user_stats_collection].find_one({'_id': ObjectId(user_id)}) or {}
    
    last_active_date = user_stats.get('lastActiveDate')
    current_streak = user_stats.get('currentStreakDays', 0)
    max_streak = user_stats.get('maxStreakDays', 0)
    weekly_activity = user_stats.get('weeklyActivity', [])
    
    # Calculate streak
    if last_active_date:
        last_date = datetime.strptime(last_active_date, '%Y-%m-%d').date()
        today_date = datetime.strptime(today, '%Y-%m-%d').date()
        yesterday = today_date - timedelta(days=1)
        
        if last_date == yesterday:
            # Consecutive day, increment streak
            current_streak += 1
        elif last_date == today_date:
            # Same day, no change (shouldn't happen due to check above)
            pass
        else:
            # Gap in days, reset streak to 1
            current_streak = 1
    else:
        # First ever session
        current_streak = 1
    
    # Update max streak
    max_streak = max(max_streak, current_streak)
    
    # Update weekly activity (keep last 7 days)
    today_found = False
    for activity in weekly_activity:
        if activity['date'] == today:
            # Ensure sessionsCount exists (for backward compatibility)
            if 'sessionsCount' not in activity:
                activity['sessionsCount'] = 0
            activity['sessionsCount'] += 1
            today_found = True
            break
    
    if not today_found:
        weekly_activity.append({'date': today, 'sessionsCount': 1})
    
    # Keep only last 7 days
    today_date = datetime.strptime(today, '%Y-%m-%d').date()
    seven_days_ago = today_date - timedelta(days=6)
    weekly_activity = [
        activity for activity in weekly_activity 
        if datetime.strptime(activity['date'], '%Y-%m-%d').date() >= seven_days_ago
    ]
    
    # Update user stats
    await db[user_stats_collection].update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {
                'lastActiveDate': today,
                'currentStreakDays': current_streak,
                'maxStreakDays': max_streak,
                'weeklyActivity': weekly_activity,
                'updatedAt': datetime.utcnow()
            },
            '$inc': {'totalSessions': 1}
        },
        upsert=True
    )

@session_router.post('/api/sessions/complete')
async def complete_session(
    data: SessionCompleteRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    db = Database.get_database()
    session_id = data.sessionId
    now = datetime.utcnow()
    
    # Initialize processing status
    processing_status = "not_required"
    processed_video_url = None
    crop_data_dict = None
    
    # Handle video cropping if cropData is provided
    if data.cropData and data.videoURL:
        try:
            logger.info(f"🎬 Processing video cropping for session {session_id}")
            processing_status = "processing"
            
            # Convert crop data to dictionary
            crop_data_dict = data.cropData.dict()
            
            # Generate output file key for processed video
            timestamp = now.strftime('%Y%m%d_%H%M%S')
            output_file_key = f"sessions/{user_id}/{session_id}/cropped_{timestamp}.mp4"
            
            # Process video cropping
            processed_video_url = await video_processing_service.crop_video(
                input_url=data.videoURL,
                crop_data=crop_data_dict,
                output_file_key=output_file_key
            )
            
            if processed_video_url:
                processing_status = "completed"
                logger.info(f"✅ Video cropping completed for session {session_id}")
            else:
                processing_status = "failed"
                logger.error(f"❌ Video cropping failed for session {session_id}")
                
        except Exception as e:
            processing_status = "failed"
            logger.error(f"❌ Error in video cropping for session {session_id}: {str(e)}")
    
    update_fields = {
        "endTime": data.endTime,
        "durationMinutes": data.durationMinutes,
        "caloriesBurned": data.caloriesBurned,
        "videoURL": data.videoURL,
        "videoFileKey": data.videoFileKey,
        "thumbnailURL": data.thumbnailURL,
        "thumbnailFileKey": data.thumbnailFileKey,
        "score": data.score,
        "stars": data.stars,
        "rating": data.rating,
        "highlightText": data.highlightText,
        "tags": data.tags,
        "status": "completed",
        "updatedAt": now,
        # New fields for video processing
        "processedVideoURL": processed_video_url,
        "cropData": crop_data_dict,
        "processingStatus": processing_status
    }
    
    # Remove None fields
    update_fields = {k: v for k, v in update_fields.items() if v is not None}
    
    result = await db[dance_sessions_collection].update_one(
        {"_id": ObjectId(session_id), "userId": ObjectId(user_id)},
        {"$set": update_fields}
    )
    
    if result.modified_count > 0:
        # Queue background video processing for mobile compatibility (NEW)
        video_url_to_process = None
        if processed_video_url:  # If cropping was done, process the cropped video
            video_url_to_process = processed_video_url
        elif data.videoURL:  # If no cropping, process the original video
            video_url_to_process = data.videoURL
        
        if video_url_to_process:
            try:
                await background_video_processor.queue_session_video_processing(
                    session_id=session_id,
                    video_url=video_url_to_process,
                    user_id=user_id
                )
                logger.info(f"🎬 Queued background video processing for session: {session_id}")
                logger.info(f"📹 Processing URL: {video_url_to_process}")
            except Exception as e:
                logger.error(f"❌ Failed to queue video processing for session {session_id}: {str(e)}")
                # Don't fail the session completion if background processing fails to queue
        
        # Update user stats and streaks using unified function
        from services.user.service import update_user_streaks_and_activity_unified
        await update_user_streaks_and_activity_unified(db, user_id, "session")
        
        # Update session-specific stats
        await update_user_stats_from_session(db, user_id, session_id)
        
        response_message = "Session completed successfully"
        if processing_status == "completed":
            response_message += " with video processing"
        elif processing_status == "failed":
            response_message += " (video processing failed, using original video)"
        
        return {"message": response_message}
    else:
        raise HTTPException(status_code=404, detail="Session not found or already completed")

async def update_user_stats_from_session(db, user_id, session_id):
    """Update user stats based on completed session data"""
    # Get current session to extract style for mostPlayedStyle logic
    session = await db[dance_sessions_collection].find_one({"_id": ObjectId(session_id)})
    style = session.get('style', '') if session else ''
    
    # Check if this session is part of a challenge submission
    challenge_submissions_collection = Database.get_collection_name('challenge_submissions')
    is_challenge_session = await db[challenge_submissions_collection].find_one({
        "sessionId": session_id
    })
    
    # Prepare stats update
    stats_update = {
        '$inc': {},
        '$set': {
            'updatedAt': datetime.utcnow()
        }
    }
    
    # Add incremental updates for non-None values from session data
    if session and session.get('caloriesBurned') is not None:
        stats_update['$inc']['totalKcal'] = session['caloriesBurned']
    if session and session.get('durationMinutes') is not None:
        stats_update['$inc']['totalTimeMinutes'] = session['durationMinutes']
    if session and session.get('stars') is not None:
        stats_update['$inc']['starsEarned'] = session['stars']
    
    # Track sessions vs challenges separately
    if is_challenge_session:
        stats_update['$inc']['totalChallenges'] = 1
    else:
        stats_update['$inc']['totalSessions'] = 1
    
    # Handle mostPlayedStyle logic (simple version - can be improved later)
    if style:
        stats_update['$set']['mostPlayedStyle'] = style
    
    # Only update if there are incremental changes
    if stats_update['$inc']:
        await db[user_stats_collection].update_one(
            {'_id': ObjectId(user_id)},
            stats_update,
            upsert=True
        )

@session_router.get('/api/sessions/me')
async def get_my_sessions(user_id: str = Depends(get_current_user_id)):
    db = Database.get_database()
    sessions = await db[dance_sessions_collection].find({"userId": ObjectId(user_id)}).sort("startTime", -1).to_list(100)
    for s in sessions:
        s['_id'] = str(s['_id'])
        s['userId'] = str(s['userId'])
    return sessions

@session_router.get('/api/sessions/feed')
async def get_public_feed(style: str = None, location: str = None, skip: int = 0, limit: int = 20):
    db = Database.get_database()
    query = {"isPublic": True, "sharedToFeed": True}
    if style:
        query["style"] = style
    if location:
        query["location"] = location
    sessions = await db[dance_sessions_collection].find(query).sort("createdAt", -1).skip(skip).limit(limit).to_list(length=limit)
    user_ids = list({s['userId'] for s in sessions})
    # Fetch all relevant users in one query
    users = await db[users_collection].find({"_id": {"$in": [ObjectId(uid) for uid in user_ids]}}).to_list(len(user_ids))
    user_map = {str(u['_id']): u for u in users}
    for s in sessions:
        s['_id'] = str(s['_id'])
        s['userId'] = str(s['userId'])
        user = user_map.get(s['userId'])
        if user:
            # Handle cases where profile might be None or missing
            profile = user.get('profile') or {}
            location_data = profile.get('location') or {}
            
            s['userProfile'] = {
                'displayName': profile.get('displayName', ''),
                'avatarUrl': profile.get('avatarUrl', ''),
                'isPro': user.get('isPro', False),
                'location': location_data.get('city', '')
            }
        else:
            s['userProfile'] = {'displayName': '', 'avatarUrl': '', 'isPro': False, 'location': ''}
        s.setdefault('videoThumbnailUrl', '')
        s.setdefault('videoDuration', 0)
        s.setdefault('likesCount', 0)
        s.setdefault('commentsCount', 0)
    return sessions 

@session_router.post('/api/sessions/{session_id}/like')
async def like_session(
    session_id: str = Path(...),
    user_id: str = Depends(get_current_user_id)
):
    db = Database.get_database()
    session_obj_id = ObjectId(session_id)
    user_obj_id = ObjectId(user_id)
    # Check if already liked
    existing = await db[session_likes_collection].find_one({"sessionId": session_obj_id, "userId": user_obj_id})
    if existing:
        return {"message": "Already liked"}
    await db[session_likes_collection].insert_one({
        "sessionId": session_obj_id,
        "userId": user_obj_id,
        "createdAt": datetime.utcnow()
    })
    await db[dance_sessions_collection].update_one({"_id": session_obj_id}, {"$inc": {"likesCount": 1}})
    return {"message": "Session liked"}

@session_router.post('/api/sessions/{session_id}/unlike')
async def unlike_session(
    session_id: str = Path(...),
    user_id: str = Depends(get_current_user_id)
):
    db = Database.get_database()
    session_obj_id = ObjectId(session_id)
    user_obj_id = ObjectId(user_id)
    result = await db[session_likes_collection].delete_one({"sessionId": session_obj_id, "userId": user_obj_id})
    if result.deleted_count:
        await db[dance_sessions_collection].update_one({"_id": session_obj_id}, {"$inc": {"likesCount": -1}})
        return {"message": "Session unliked"}
    return {"message": "Session was not liked"}

@session_router.get('/api/sessions/{session_id}/likes')
async def get_session_likers(
    session_id: str = Path(...),
    skip: int = 0,
    limit: int = 20
):
    db = Database.get_database()
    session_obj_id = ObjectId(session_id)
    likes = await db[session_likes_collection].find({"sessionId": session_obj_id}).skip(skip).limit(limit).to_list(length=limit)
    user_ids = [like['userId'] for like in likes]
    users = await db[users_collection].find({"_id": {"$in": user_ids}}).to_list(len(user_ids))
    user_map = {u['_id']: u for u in users}
    result = []
    for like in likes:
        user = user_map.get(like['userId'])
        if user:
            # Handle cases where profile might be None or missing
            profile = user.get('profile') or {}
            location_data = profile.get('location') or {}
            
            result.append({
                'userId': str(user['_id']),
                'displayName': profile.get('displayName', ''),
                'avatarUrl': profile.get('avatarUrl', ''),
                'isPro': user.get('isPro', False),
                'location': location_data.get('city', '')
            })
    return result 