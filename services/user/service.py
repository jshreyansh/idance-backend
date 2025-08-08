from fastapi import APIRouter, Depends, HTTPException, status, Header, Body
from services.user.models import UserProfileUpdate, UserStatsUpdateRequest, UserStatsResponse
from infra.mongo import Database
from datetime import datetime, timedelta
from jose import jwt, JWTError
from bson import ObjectId
from typing import List, Dict, Optional
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey123")
JWT_ALGORITHM = "HS256"

user_router = APIRouter()

def get_current_user_id(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@user_router.get('/user/health')
async def user_health():
    return {"status": "user service ok"}

@user_router.get('/user/list')
async def list_users():
    db = Database.get_database()
    users = await db['users'].find().to_list(100)
    return users

@user_router.post('/user/create')
async def create_user(user: dict):
    db = Database.get_database()
    result = await db['users'].insert_one(user)
    return {"inserted_id": str(result.inserted_id)}

@user_router.patch("/user/profile")
async def update_profile(
    profile: UserProfileUpdate,
    user_id: str = Depends(get_current_user_id)
):
    db = Database.get_database()
    update_fields = {f"profile.{k}": v for k, v in profile.dict(exclude_unset=True).items()}
    update_fields["updatedAt"] = datetime.utcnow()
    # Unique username validation
    if profile.username:
        existing = await db["users"].find_one({"profile.username": profile.username, "_id": {"$ne": ObjectId(user_id)}})
        if existing:
            raise HTTPException(status_code=409, detail="Username already taken")
    result = await db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success"} 

@user_router.get('/user/me')
async def get_my_user_data(user_id: str = Depends(get_current_user_id)):
    db = Database.get_database()
    user = await db['users'].find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    user['_id'] = str(user['_id'])
    user.pop('password', None)
    return user

stats_router = APIRouter()

@stats_router.get('/api/stats/me', response_model=UserStatsResponse)
async def get_my_stats(user_id: str = Depends(get_current_user_id)):
    db = Database.get_database()
    stats = await db['user_stats'].find_one({'_id': ObjectId(user_id)})
    
    if not stats:
        # Initialize with calculated values
        total_activities = await calculate_total_activities(db, user_id)
        
        # Count individual activities
        sessions_count = await db['dance_sessions'].count_documents({
            "userId": ObjectId(user_id),
            "status": "completed"
        })
        
        challenges_count = await db['challenge_submissions'].count_documents({
            "userId": user_id
        })
        
        breakdowns_count = await db['dance_breakdowns'].count_documents({
            "userId": ObjectId(user_id),
            "success": True
        })
        
        return UserStatsResponse(
            totalActivities=total_activities,
            totalSessions=sessions_count,
            totalChallenges=challenges_count,
            totalBreakdowns=breakdowns_count
        )
    
    stats.pop('_id', None)
    
    # Calculate current activity counts
    total_activities = await calculate_total_activities(db, user_id)
    sessions_count = await db['dance_sessions'].count_documents({
        "userId": ObjectId(user_id),
        "status": "completed"
    })
    challenges_count = await db['challenge_submissions'].count_documents({
        "userId": user_id
    })
    breakdowns_count = await db['dance_breakdowns'].count_documents({
        "userId": ObjectId(user_id),
        "success": True
    })
    
    # Update stats with calculated values
    stats.update({
        'totalActivities': total_activities,
        'totalSessions': sessions_count,
        'totalChallenges': challenges_count,
        'totalBreakdowns': breakdowns_count
    })
    
    return UserStatsResponse(**stats)

async def calculate_total_activities(db, user_id: str) -> int:
    """Calculate total activities by summing sessions, challenges, and breakdowns"""
    try:
        # Count sessions
        sessions_count = await db['dance_sessions'].count_documents({
            "userId": ObjectId(user_id),
            "status": "completed"
        })
        
        # Count challenges
        challenges_count = await db['challenge_submissions'].count_documents({
            "userId": user_id
        })
        
        # Count breakdowns
        breakdowns_count = await db['dance_breakdowns'].count_documents({
            "userId": ObjectId(user_id),
            "success": True
        })
        
        return sessions_count + challenges_count + breakdowns_count
        
    except Exception as e:
        logging.error(f"Error calculating total activities: {e}")
        return 0

@stats_router.post('/api/stats/update')
async def update_my_stats(
    update: UserStatsUpdateRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    db = Database.get_database()
    
    # Calculate total activities
    total_activities = await calculate_total_activities(db, user_id)
    
    update_dict = {
        '$inc': {
            'totalKcal': update.kcal,
            'totalTimeMinutes': update.minutes,
            'totalSteps': update.steps,
            'totalSessions': 1,
            'starsEarned': update.stars
        },
        '$set': {
            'updatedAt': datetime.utcnow(),
            'mostPlayedStyle': update.style,  # Optionally, improve this logic later
            'totalActivities': total_activities
        }
    }
    await db['user_stats'].update_one(
        {'_id': ObjectId(user_id)},
        update_dict,
        upsert=True
    )
    return {'message': 'Stats updated'} 

class HeatmapResponse(BaseModel):
    date: str
    sessionsCount: int
    isActive: bool
    caloriesBurned: int = 0

@stats_router.get('/api/stats/heatmap', response_model=List[HeatmapResponse])
async def get_activity_heatmap(
    days: int = 7,
    user_id: str = Depends(get_current_user_id)
):
    db = Database.get_database()
    stats = await db['user_stats'].find_one({'_id': ObjectId(user_id)})
    
    # Get weekly activity data
    weekly_activity = stats.get('weeklyActivity', []) if stats else []
    activity_map = {activity['date']: activity['sessionsCount'] for activity in weekly_activity}
    
    # Get calories data from completed sessions for the date range
    today = datetime.now().date()
    start_date = today - timedelta(days=days-1)
    
    # Query sessions in the date range to get calories per day
    sessions = await db['dance_sessions'].find({
        "userId": ObjectId(user_id),
        "status": "completed",
        "startTime": {
            "$gte": datetime.combine(start_date, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
        }
    }).to_list(1000)
    
    # Query challenge submissions in the date range
    challenge_submissions = await db['challenge_submissions'].find({
        "userId": user_id,
        "timestamps.submittedAt": {
            "$gte": datetime.combine(start_date, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
        }
    }).to_list(1000)
    
    # Calculate calories per day
    calories_per_day = {}
    for session in sessions:
        session_date = session['startTime'].date().strftime('%Y-%m-%d')
        calories = session.get('caloriesBurned', 0) or 0
        calories_per_day[session_date] = calories_per_day.get(session_date, 0) + calories
    
    # Calculate sessions count per day (including challenges)
    sessions_count_per_day = {}
    
    # Count regular sessions
    for session in sessions:
        session_date = session['startTime'].date().strftime('%Y-%m-%d')
        sessions_count_per_day[session_date] = sessions_count_per_day.get(session_date, 0) + 1
    
    # Count challenge submissions
    for submission in challenge_submissions:
        submitted_at = submission.get('timestamps', {}).get('submittedAt')
        if submitted_at:
            submission_date = submitted_at.date().strftime('%Y-%m-%d')
            sessions_count_per_day[submission_date] = sessions_count_per_day.get(submission_date, 0) + 1
    
    # Generate last N days with calories data
    result = []
    for i in range(days - 1, -1, -1):  # Reverse order to get oldest to newest
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        sessions_count = sessions_count_per_day.get(date_str, 0)  # Use actual count instead of weeklyActivity
        calories_burned = calories_per_day.get(date_str, 0)
        result.append(HeatmapResponse(
            date=date_str,
            sessionsCount=sessions_count,
            isActive=sessions_count > 0,
            caloriesBurned=calories_burned
        ))
    
    return result 

@user_router.get('/api/user/history', response_model=Dict)
async def get_user_history(
    page: int = 1,
    limit: int = 20,
    activity_type: Optional[str] = None,  # 'session', 'challenge', 'breakdown', or None for all
    user_id: str = Depends(get_current_user_id)
):
    """
    Get unified user history combining sessions, challenges, and dance breakdowns
    Each activity type has different metadata for frontend display
    """
    try:
        db = Database.get_database()
        skip = (page - 1) * limit
        
        # Initialize results
        all_activities = []
        
        # 1. Get Dance Sessions
        if not activity_type or activity_type == 'session':
            sessions = await db['dance_sessions'].find(
                {"userId": ObjectId(user_id)},
                {
                    "startTime": 1,
                    "endTime": 1,
                    "durationMinutes": 1,
                    "caloriesBurned": 1,
                    "videoUrl": 1,
                    "thumbnailUrl": 1,
                    "danceStyle": 1,
                    "score": 1,
                    "level": 1
                }
            ).sort("startTime", -1).skip(skip).limit(limit).to_list(length=limit)
            
            for session in sessions:
                session['_id'] = str(session['_id'])
                session['activityType'] = 'session'
                session['activityTitle'] = f"{session.get('danceStyle', 'Dance')} Session"
                session['activitySubtitle'] = f"{session.get('durationMinutes', 0)} min • {session.get('caloriesBurned', 0)} cal"
                session['timestamp'] = session.get('startTime')
                session['previewImage'] = session.get('thumbnailUrl') or session.get('videoUrl', '')
                session['metadata'] = {
                    "duration": session.get('durationMinutes', 0),
                    "calories": session.get('caloriesBurned', 0),
                    "style": session.get('danceStyle', 'Unknown'),
                    "score": session.get('score', 0),
                    "level": session.get('level', 1)
                }
                all_activities.append(session)
        
        # 2. Get Challenge Submissions
        if not activity_type or activity_type == 'challenge':
            challenges = await db['challenge_submissions'].find(
                {"userId": ObjectId(user_id)},
                {
                    "challengeId": 1,
                    "videoUrl": 1,
                    "thumbnailUrl": 1,
                    "score": 1,
                    "timestamps": 1,
                    "durationMinutes": 1,
                    "caloriesBurned": 1,
                    "challenge": 1  # Will be populated via lookup
                }
            ).sort("timestamps.submittedAt", -1).skip(skip).limit(limit).to_list(length=limit)
            
            # Get challenge details for each submission
            for challenge_submission in challenges:
                challenge_id = challenge_submission.get('challengeId')
                if challenge_id:
                    challenge = await db['challenges'].find_one({"_id": ObjectId(challenge_id)})
                    if challenge:
                        challenge_submission['challenge'] = challenge
                
                challenge_submission['_id'] = str(challenge_submission['_id'])
                challenge_submission['activityType'] = 'challenge'
                challenge_submission['activityTitle'] = challenge_submission.get('challenge', {}).get('title', 'Challenge Submission')
                challenge_submission['activitySubtitle'] = f"Score: {challenge_submission.get('score', 0)} • {challenge_submission.get('durationMinutes', 0)} min"
                challenge_submission['timestamp'] = challenge_submission.get('timestamps', {}).get('submittedAt')
                challenge_submission['previewImage'] = challenge_submission.get('thumbnailUrl') or challenge_submission.get('videoUrl', '')
                challenge_submission['metadata'] = {
                    "score": challenge_submission.get('score', 0),
                    "duration": challenge_submission.get('durationMinutes', 0),
                    "calories": challenge_submission.get('caloriesBurned', 0),
                    "challengeTitle": challenge_submission.get('challenge', {}).get('title', ''),
                    "challengeType": challenge_submission.get('challenge', {}).get('type', ''),
                    "points": challenge_submission.get('challenge', {}).get('points', 0)
                }
                all_activities.append(challenge_submission)
        
        # 3. Get Dance Breakdowns
        if not activity_type or activity_type == 'breakdown':
            breakdowns = await db['dance_breakdowns'].find(
                {"userId": ObjectId(user_id)},
                {
                    "videoUrl": 1,
                    "playableVideoUrl": 1,
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
                breakdown['activityTitle'] = breakdown.get('title', 'Dance Breakdown')
                breakdown['activitySubtitle'] = f"{breakdown.get('totalSteps', 0)} steps • {breakdown.get('difficultyLevel', 'Intermediate')}"
                breakdown['timestamp'] = breakdown.get('createdAt')
                breakdown['previewImage'] = breakdown.get('playableVideoUrl') or breakdown.get('videoUrl', '')
                breakdown['metadata'] = {
                    "totalSteps": breakdown.get('totalSteps', 0),
                    "duration": breakdown.get('duration', 0),
                    "difficulty": breakdown.get('difficultyLevel', 'Intermediate'),
                    "originalUrl": breakdown.get('videoUrl', ''),
                    "playableUrl": breakdown.get('playableVideoUrl', '')
                }
                all_activities.append(breakdown)
        
        # Sort all activities by timestamp (most recent first)
        all_activities.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        
        # Apply pagination to combined results
        start_idx = skip
        end_idx = start_idx + limit
        paginated_activities = all_activities[start_idx:end_idx]
        
        # Get total counts for each activity type
        total_sessions = await db['dance_sessions'].count_documents({"userId": ObjectId(user_id)})
        total_challenges = await db['challenge_submissions'].count_documents({"userId": ObjectId(user_id)})
        total_breakdowns = await db['dance_breakdowns'].count_documents({"userId": ObjectId(user_id)})
        
        return {
            "activities": paginated_activities,
            "total": len(all_activities),
            "page": page,
            "limit": limit,
            "hasMore": len(all_activities) > (page * limit),
            "summary": {
                "sessions": total_sessions,
                "challenges": total_challenges,
                "breakdowns": total_breakdowns,
                "total": total_sessions + total_challenges + total_breakdowns
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get user history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user history: {str(e)}") 