from fastapi import APIRouter, Depends, HTTPException, Body, Path
from services.session.models import SessionStartRequest, SessionCompleteRequest, SessionResponse
from infra.mongo import Database
from datetime import datetime, timedelta
from bson import ObjectId
from services.user.service import get_current_user_id

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
    user = await db['users'].find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    profile = user.get('profile', {})
    userProfile = {
        'displayName': profile.get('displayName', ''),
        'avatarUrl': profile.get('avatarUrl', ''),
        'isPro': user.get('isPro', False),
        'location': profile.get('location', {}).get('city', '')
    }
    
    # Check if user already had a session today
    existing_session_today = await db['dance_sessions'].find_one({
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
    result = await db['dance_sessions'].insert_one(session_doc)
    return {"sessionId": str(result.inserted_id)}

async def update_user_streaks_and_activity(db, user_id, today):
    user_stats = await db['user_stats'].find_one({'_id': ObjectId(user_id)}) or {}
    
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
    await db['user_stats'].update_one(
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
        "updatedAt": now
    }
    # Remove None fields
    update_fields = {k: v for k, v in update_fields.items() if v is not None}
    result = await db['dance_sessions'].update_one(
        {"_id": ObjectId(session_id), "userId": ObjectId(user_id)},
        {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found or not owned by user")
    
    # Update user stats with session data
    await update_user_stats_from_session(db, user_id, data)
    
    return {"message": "Session completed"}

async def update_user_stats_from_session(db, user_id, session_data):
    """Update user stats based on completed session data"""
    # Get current session to extract style for mostPlayedStyle logic
    session = await db['dance_sessions'].find_one({"_id": ObjectId(session_data.sessionId)})
    style = session.get('style', '') if session else ''
    
    # Prepare stats update
    stats_update = {
        '$inc': {},
        '$set': {
            'updatedAt': datetime.utcnow()
        }
    }
    
    # Add incremental updates for non-None values
    if session_data.caloriesBurned is not None:
        stats_update['$inc']['totalKcal'] = session_data.caloriesBurned
    if session_data.durationMinutes is not None:
        stats_update['$inc']['totalTimeMinutes'] = session_data.durationMinutes
    if session_data.stars is not None:
        stats_update['$inc']['starsEarned'] = session_data.stars
    
    # Handle mostPlayedStyle logic (simple version - can be improved later)
    if style:
        stats_update['$set']['mostPlayedStyle'] = style
    
    # Only update if there are incremental changes
    if stats_update['$inc']:
        await db['user_stats'].update_one(
            {'_id': ObjectId(user_id)},
            stats_update,
            upsert=True
        )

@session_router.get('/api/activities/me')
async def get_my_activities(
    user_id: str = Depends(get_current_user_id),
    page: int = 1,
    limit: int = 20,
    activity_type: str = None  # 'sessions', 'challenges', 'breakdowns', or None for all
):
    """
    Get all user activities (sessions, challenges, breakdowns) unified
    """
    try:
        db = Database.get_database()
        skip = (page - 1) * limit
        
        activities = []
        
        # Get sessions
        if activity_type is None or activity_type == 'sessions':
            sessions = await db['dance_sessions'].find(
                {"userId": ObjectId(user_id)},
                {
                    "startTime": 1,
                    "endTime": 1,
                    "style": 1,
                    "sessionType": 1,
                    "durationMinutes": 1,
                    "caloriesBurned": 1,
                    "isPublic": 1,
                    "videoThumbnailUrl": 1,
                    "likesCount": 1,
                    "commentsCount": 1,
                    "status": 1
                }
            ).sort("startTime", -1).skip(skip).limit(limit).to_list(length=limit)
            
            for session in sessions:
                session['_id'] = str(session['_id'])
                session['activityType'] = 'session'
                session['activityDate'] = session['startTime']
                session['title'] = f"{session.get('style', 'Dance')} Session"
                session['description'] = f"{session.get('durationMinutes', 0)} minutes • {session.get('caloriesBurned', 0)} calories"
                activities.append(session)
        
        # Get challenge submissions
        if activity_type is None or activity_type == 'challenges':
            challenges = await db['challenge_submissions'].find(
                {"userId": ObjectId(user_id)},
                {
                    "challengeId": 1,
                    "videoUrl": 1,
                    "durationMinutes": 1,
                    "caloriesBurned": 1,
                    "score": 1,
                    "timestamps.submittedAt": 1,
                    "isPublic": 1
                }
            ).sort("timestamps.submittedAt", -1).skip(skip).limit(limit).to_list(length=limit)
            
            for challenge in challenges:
                challenge['_id'] = str(challenge['_id'])
                challenge['activityType'] = 'challenge'
                challenge['activityDate'] = challenge.get('timestamps', {}).get('submittedAt')
                challenge['title'] = "Challenge Submission"
                challenge['description'] = f"{challenge.get('durationMinutes', 0)} minutes • {challenge.get('caloriesBurned', 0)} calories"
                activities.append(challenge)
        
        # Get dance breakdowns
        if activity_type is None or activity_type == 'breakdowns':
            breakdowns = await db['dance_breakdowns'].find(
                {"userId": ObjectId(user_id)},
                {
                    "videoUrl": 1,
                    "title": 1,
                    "duration": 1,
                    "totalSteps": 1,
                    "difficultyLevel": 1,
                    "createdAt": 1,
                    "success": 1
                }
            ).sort("createdAt", -1).skip(skip).limit(limit).to_list(length=limit)
            
            for breakdown in breakdowns:
                breakdown['_id'] = str(breakdown['_id'])
                breakdown['activityType'] = 'breakdown'
                breakdown['activityDate'] = breakdown['createdAt']
                breakdown['title'] = breakdown.get('title', 'Dance Breakdown')
                breakdown['description'] = f"{breakdown.get('totalSteps', 0)} steps • {breakdown.get('difficultyLevel', 'Intermediate')}"
                activities.append(breakdown)
        
        # Sort all activities by date (most recent first)
        activities.sort(key=lambda x: x['activityDate'], reverse=True)
        
        # Apply pagination to combined results
        start_idx = skip
        end_idx = start_idx + limit
        paginated_activities = activities[start_idx:end_idx]
        
        # Get total counts for each type
        total_sessions = await db['dance_sessions'].count_documents({"userId": ObjectId(user_id)})
        total_challenges = await db['challenge_submissions'].count_documents({"userId": ObjectId(user_id)})
        total_breakdowns = await db['dance_breakdowns'].count_documents({"userId": ObjectId(user_id)})
        
        return {
            "activities": paginated_activities,
            "total": len(activities),
            "page": page,
            "limit": limit,
            "hasMore": end_idx < len(activities),
            "counts": {
                "sessions": total_sessions,
                "challenges": total_challenges,
                "breakdowns": total_breakdowns,
                "total": total_sessions + total_challenges + total_breakdowns
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activities: {str(e)}")

@session_router.get('/api/sessions/me')
async def get_my_sessions(user_id: str = Depends(get_current_user_id)):
    db = Database.get_database()
    sessions = await db['dance_sessions'].find({"userId": ObjectId(user_id)}).sort("startTime", -1).to_list(100)
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
    sessions = await db['dance_sessions'].find(query).sort("createdAt", -1).skip(skip).limit(limit).to_list(length=limit)
    user_ids = list({s['userId'] for s in sessions})
    # Fetch all relevant users in one query
    users = await db['users'].find({"_id": {"$in": [ObjectId(uid) for uid in user_ids]}}).to_list(len(user_ids))
    user_map = {str(u['_id']): u for u in users}
    for s in sessions:
        s['_id'] = str(s['_id'])
        s['userId'] = str(s['userId'])
        user = user_map.get(s['userId'])
        if user:
            profile = user.get('profile', {})
            s['userProfile'] = {
                'displayName': profile.get('displayName', ''),
                'avatarUrl': profile.get('avatarUrl', ''),
                'isPro': user.get('isPro', False),
                'location': profile.get('location', {}).get('city', '')
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
    existing = await db['session_likes'].find_one({"sessionId": session_obj_id, "userId": user_obj_id})
    if existing:
        return {"message": "Already liked"}
    await db['session_likes'].insert_one({
        "sessionId": session_obj_id,
        "userId": user_obj_id,
        "createdAt": datetime.utcnow()
    })
    await db['dance_sessions'].update_one({"_id": session_obj_id}, {"$inc": {"likesCount": 1}})
    return {"message": "Session liked"}

@session_router.post('/api/sessions/{session_id}/unlike')
async def unlike_session(
    session_id: str = Path(...),
    user_id: str = Depends(get_current_user_id)
):
    db = Database.get_database()
    session_obj_id = ObjectId(session_id)
    user_obj_id = ObjectId(user_id)
    result = await db['session_likes'].delete_one({"sessionId": session_obj_id, "userId": user_obj_id})
    if result.deleted_count:
        await db['dance_sessions'].update_one({"_id": session_obj_id}, {"$inc": {"likesCount": -1}})
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
    likes = await db['session_likes'].find({"sessionId": session_obj_id}).skip(skip).limit(limit).to_list(length=limit)
    user_ids = [like['userId'] for like in likes]
    users = await db['users'].find({"_id": {"$in": user_ids}}).to_list(len(user_ids))
    user_map = {u['_id']: u for u in users}
    result = []
    for like in likes:
        user = user_map.get(like['userId'])
        if user:
            profile = user.get('profile', {})
            result.append({
                'userId': str(user['_id']),
                'displayName': profile.get('displayName', ''),
                'avatarUrl': profile.get('avatarUrl', ''),
                'isPro': user.get('isPro', False),
                'location': profile.get('location', {}).get('city', '')
            })
    return result 