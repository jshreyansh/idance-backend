from fastapi import APIRouter, Depends, HTTPException, status, Header, Body
from services.user.models import UserProfileUpdate, UserStatsUpdateRequest, UserStatsResponse
from infra.mongo import Database
# Environment-aware collection names
users_collection = Database.get_collection_name('users')
user_stats_collection = Database.get_collection_name('user_stats')
challenges_collection = Database.get_collection_name('challenges')
challenge_submissions_collection = Database.get_collection_name('challenge_submissions')
dance_sessions_collection = Database.get_collection_name('dance_sessions')
dance_breakdowns_collection = Database.get_collection_name('dance_breakdowns')

from datetime import datetime, timedelta
from jose import jwt, JWTError
from bson import ObjectId
from typing import List, Dict, Optional
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

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
    users = await db[users_collection].find().to_list(100)
    return users

@user_router.post('/user/create')
async def create_user(user: dict):
    db = Database.get_database()
    result = await db[users_collection].insert_one(user)
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
        existing = await db[users_collection].find_one({"profile.username": profile.username, "_id": {"$ne": ObjectId(user_id)}})
        if existing:
            raise HTTPException(status_code=409, detail="Username already taken")
    result = await db[users_collection].update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success"} 

@user_router.get('/user/me')
async def get_my_user_data(user_id: str = Depends(get_current_user_id)):
    db = Database.get_database()
    user = await db[users_collection].find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    user['_id'] = str(user['_id'])
    user.pop('password', None)
    return user

stats_router = APIRouter()

@stats_router.get('/api/stats/me', response_model=UserStatsResponse)
async def get_my_stats(user_id: str = Depends(get_current_user_id)):
    """
    Get comprehensive user stats calculated from actual activity data
    """
    db = Database.get_database()
    stats = await db[user_stats_collection].find_one({'_id': ObjectId(user_id)})
    
    # Calculate all stats from actual data
    total_activities, sessions_count, challenges_count, breakdowns_count = await calculate_activity_counts(db, user_id)
    total_kcal, total_time_minutes, total_steps, stars_earned = await calculate_fitness_metrics(db, user_id)
    
    if not stats:
        # Initialize with calculated values
        return UserStatsResponse(
            totalActivities=total_activities,
            totalSessions=sessions_count,
            totalChallenges=challenges_count,
            totalBreakdowns=breakdowns_count,
            totalKcal=total_kcal,
            totalTimeMinutes=total_time_minutes,
            totalSteps=total_steps,
            starsEarned=stars_earned
        )
    
    stats.pop('_id', None)
    
    # Update stats with calculated values
    stats.update({
        'totalActivities': total_activities,
        'totalSessions': sessions_count,
        'totalChallenges': challenges_count,
        'totalBreakdowns': breakdowns_count,
        'totalKcal': total_kcal,
        'totalTimeMinutes': total_time_minutes,
        'totalSteps': total_steps,
        'starsEarned': stars_earned
    })
    
    return UserStatsResponse(**stats)

async def calculate_activity_counts(db, user_id: str) -> tuple:
    """Calculate activity counts by summing sessions, challenges, and breakdowns"""
    try:
        # Count sessions
        sessions_count = await db[dance_sessions_collection].count_documents({
            "userId": ObjectId(user_id),
            "status": "completed"
        })
        
        # Count challenges
        challenges_count = await db[challenge_submissions_collection].count_documents({
            "userId": user_id
        })
        
        # Count breakdowns
        breakdowns_count = await db[dance_breakdowns_collection].count_documents({
            "userId": ObjectId(user_id),
            "success": True
        })
        
        total_activities = sessions_count + challenges_count + breakdowns_count
        return total_activities, sessions_count, challenges_count, breakdowns_count
        
    except Exception as e:
        logging.error(f"Error calculating activity counts: {e}")
        return 0, 0, 0, 0

async def calculate_fitness_metrics(db, user_id: str) -> tuple:
    """Calculate fitness metrics from actual activity data"""
    try:
        total_kcal = 0
        total_time_minutes = 0
        total_steps = 0
        stars_earned = 0
        
        # Calculate from sessions
        sessions = await db[dance_sessions_collection].find({
            "userId": ObjectId(user_id),
            "status": "completed"
        }).to_list(1000)
        
        for session in sessions:
            total_kcal += session.get('caloriesBurned', 0) or 0
            total_time_minutes += session.get('durationMinutes', 0) or 0
            total_steps += session.get('steps', 0) or 0
            stars_earned += session.get('stars', 0) or 0
        
        # Calculate from challenges
        challenges = await db[challenge_submissions_collection].find({
            "userId": user_id
        }).to_list(1000)
        
        for challenge in challenges:
            # Get video data for duration and calories
            video_data = challenge.get('videoData', {})
            if video_data:
                duration_seconds = video_data.get('duration', 0) or 0
                duration_minutes = int(duration_seconds / 60) if duration_seconds > 0 else 0
                total_time_minutes += duration_minutes
                
                # Calculate calories based on challenge type
                challenge_type = challenge.get('challengeType', 'freestyle')
                if challenge_type == "freestyle":
                    calories = int(duration_minutes * 5)  # 5 calories per minute
                elif challenge_type == "static":
                    calories = int(duration_minutes * 3)  # 3 calories per minute
                else:
                    calories = int(duration_minutes * 4)  # 4 calories per minute
                total_kcal += calories
            
            # Add stars from challenge
            stars_earned += challenge.get('stars', 0) or 0
        
        # Calculate from dance breakdowns
        breakdowns = await db[dance_breakdowns_collection].find({
            "userId": ObjectId(user_id),
            "success": True
        }).to_list(1000)
        
        for breakdown in breakdowns:
            # Get duration from breakdown
            duration_seconds = breakdown.get('duration', 0) or 0
            duration_minutes = int(duration_seconds / 60) if duration_seconds > 0 else 0
            total_time_minutes += duration_minutes
            
            # Calculate calories for breakdown (analysis activity)
            calories = int(duration_minutes * 4)  # 4 calories per minute for analysis
            total_kcal += calories
        
        return total_kcal, total_time_minutes, total_steps, stars_earned
        
    except Exception as e:
        logging.error(f"Error calculating fitness metrics: {e}")
        return 0, 0, 0, 0

@stats_router.post('/api/stats/update')
async def update_my_stats(
    update: UserStatsUpdateRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update user stats manually (legacy endpoint - stats are now calculated from actual data)
    """
    db = Database.get_database()
    
    # Calculate total activities
    total_activities, _, _, _ = await calculate_activity_counts(db, user_id)
    
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
    await db[user_stats_collection].update_one(
        {'_id': ObjectId(user_id)},
        update_dict,
        upsert=True
    )
    return {'message': 'Stats updated'} 

async def update_user_streaks_and_activity_unified(db, user_id: str, activity_type: str = "session"):
    """
    Unified function to update streaks and weekly activity for ALL activity types
    Called by sessions, challenges, and breakdowns
    """
    try:
        user_stats = await db[user_stats_collection].find_one({'_id': ObjectId(user_id)}) or {}
        
        last_active_date = user_stats.get('lastActiveDate')
        current_streak = user_stats.get('currentStreakDays', 0)
        max_streak = user_stats.get('maxStreakDays', 0)
        weekly_activity = user_stats.get('weeklyActivity', [])
        
        # Calculate streak
        today = datetime.utcnow().strftime('%Y-%m-%d')
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
            # First ever activity
            current_streak = 1
        
        # Update max streak
        max_streak = max(max_streak, current_streak)
        
        # Update weekly activity (keep last 7 days)
        today_found = False
        for activity in weekly_activity:
            if activity['date'] == today:
                # Handle both old and new field names for backward compatibility
                if 'activitiesCount' in activity:
                    activity['activitiesCount'] += 1
                elif 'sessionsCount' in activity:
                    # Migrate old data to new field name
                    activity['activitiesCount'] = activity.get('sessionsCount', 0) + 1
                    activity.pop('sessionsCount', None)  # Remove old field
                else:
                    activity['activitiesCount'] = 1
                today_found = True
                break
        
        if not today_found:
            weekly_activity.append({'date': today, 'activitiesCount': 1})
        
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
                '$inc': {'totalActivities': 1}  # ✅ Track total activities instead of just sessions
            },
            upsert=True
        )
        
        logger.info(f"✅ Updated streaks and activity for user {user_id}, activity type: {activity_type}")
        
    except Exception as e:
        logger.error(f"❌ Error updating streaks and activity for user {user_id}: {str(e)}")
        raise

class HeatmapResponse(BaseModel):
    date: str
    activitiesCount: int  # Total activities (sessions + challenges + breakdowns)
    isActive: bool
    caloriesBurned: int = 0

@stats_router.get('/api/stats/heatmap', response_model=List[HeatmapResponse])
async def get_activity_heatmap(
    days: int = 7,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get activity heatmap data showing total activities (sessions + challenges + breakdowns) per day
    """
    db = Database.get_database()
    stats = await db[user_stats_collection].find_one({'_id': ObjectId(user_id)})
    
    # Get weekly activity data (this already tracks total activities)
    weekly_activity = stats.get('weeklyActivity', []) if stats else []
    activity_map = {activity['date']: activity.get('activitiesCount', activity.get('sessionsCount', 0)) for activity in weekly_activity}
    
    # Get calories data from completed sessions for the date range
    today = datetime.now().date()
    start_date = today - timedelta(days=days-1)
    
    # Query sessions in the date range to get calories per day
    sessions = await db[dance_sessions_collection].find({
        "userId": ObjectId(user_id),
        "status": "completed",
        "startTime": {
            "$gte": datetime.combine(start_date, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
        }
    }).to_list(1000)
    
    # Query challenge submissions in the date range
    challenge_submissions = await db[challenge_submissions_collection].find({
        "userId": user_id,
        "timestamps.submittedAt": {
            "$gte": datetime.combine(start_date, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
        }
    }).to_list(1000)
    
    # Query dance breakdowns in the date range
    dance_breakdowns = await db[dance_breakdowns_collection].find({
        "userId": ObjectId(user_id),
        "success": True,
        "createdAt": {
            "$gte": datetime.combine(start_date, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
        }
    }).to_list(1000)
    
    # Calculate calories per day (only from sessions)
    calories_per_day = {}
    for session in sessions:
        session_date = session['startTime'].date().strftime('%Y-%m-%d')
        calories = session.get('caloriesBurned', 0) or 0
        calories_per_day[session_date] = calories_per_day.get(session_date, 0) + calories
    
    # Calculate total activities count per day (sessions + challenges + breakdowns)
    activities_count_per_day = {}
    
    # Count regular sessions
    for session in sessions:
        session_date = session['startTime'].date().strftime('%Y-%m-%d')
        activities_count_per_day[session_date] = activities_count_per_day.get(session_date, 0) + 1
    
    # Count challenge submissions
    for submission in challenge_submissions:
        submitted_at = submission.get('timestamps', {}).get('submittedAt')
        if submitted_at:
            submission_date = submitted_at.date().strftime('%Y-%m-%d')
            activities_count_per_day[submission_date] = activities_count_per_day.get(submission_date, 0) + 1
    
    # Count dance breakdowns
    for breakdown in dance_breakdowns:
        breakdown_date = breakdown['createdAt'].date().strftime('%Y-%m-%d')
        activities_count_per_day[breakdown_date] = activities_count_per_day.get(breakdown_date, 0) + 1
    
    # Generate last N days with activities and calories data
    result = []
    for i in range(days - 1, -1, -1):  # Reverse order to get oldest to newest
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        activities_count = activities_count_per_day.get(date_str, 0)  # Total activities for this day
        calories_burned = calories_per_day.get(date_str, 0)
        result.append(HeatmapResponse(
            date=date_str,
            activitiesCount=activities_count,  # Total activities (sessions + challenges + breakdowns)
            isActive=activities_count > 0,
            caloriesBurned=calories_burned
        ))
    
    return result 

@user_router.get('/api/user/history', response_model=Dict)
async def get_user_history(
    page: int = 1,
    limit: int = 20,
    activity_type: Optional[str] = None,  # 'session', 'challenge', 'breakdown', 'all', or None for all
    user_id: str = Depends(get_current_user_id)
):
    """
    Get unified user history with section-based pagination
    Supports filtering by activity type and proper pagination per section
    """
    try:
        db = Database.get_database()
        skip = (page - 1) * limit
        
        # Initialize results
        all_activities = []
        
        # Get total counts for each section
        sessions_count = await db[dance_sessions_collection].count_documents({"userId": ObjectId(user_id)})
        challenges_count = await db[challenge_submissions_collection].count_documents({"userId": user_id})
        breakdowns_count = await db[dance_breakdowns_collection].count_documents({"userId": ObjectId(user_id), "success": True})
        total_activities = sessions_count + challenges_count + breakdowns_count
        
        # 1. Get Dance Sessions
        if not activity_type or activity_type in ['session', 'all']:
            sessions = await db[dance_sessions_collection].find(
                {"userId": ObjectId(user_id)},
                {
                    "startTime": 1,
                    "endTime": 1,
                    "durationMinutes": 1,
                    "caloriesBurned": 1,
                    "videoURL": 1,  # Correct field name
                    "thumbnailURL": 1,  # Correct field name
                    "style": 1,
                    "score": 1,
                    "sessionType": 1
                }
            ).sort("startTime", -1).skip(skip if activity_type == 'session' else 0).limit(limit if activity_type == 'session' else limit).to_list(length=limit)
            
            for session in sessions:
                session['_id'] = str(session['_id'])
                session['activityType'] = 'session'
                session['activityTitle'] = 'Dance Session'
                session['activitySubtitle'] = f"{session.get('durationMinutes', 0)} min • {session.get('caloriesBurned', 0)} cal"
                session['timestamp'] = session.get('startTime')
                session['previewImage'] = session.get('thumbnailURL') or session.get('videoURL', '')
                
                # Ensure userId is converted to string if it's an ObjectId
                if 'userId' in session and isinstance(session['userId'], ObjectId):
                    session['userId'] = str(session['userId'])
                
                # Add video URLs to the response
                session['videoUrl'] = session.get('videoURL', '')
                session['thumbnailUrl'] = session.get('thumbnailURL', '')
                
                session['metadata'] = {
                    "duration": session.get('durationMinutes', 0),
                    "calories": session.get('caloriesBurned', 0),
                    "style": session.get('style', 'Unknown'),
                    "score": session.get('score', 0),
                    "level": 1,
                    "videoUrl": session.get('videoURL', ''),
                    "thumbnailUrl": session.get('thumbnailURL', '')
                }
                all_activities.append(session)
        
        # 2. Get Challenge Submissions
        if not activity_type or activity_type in ['challenge', 'all']:
            challenges = await db[challenge_submissions_collection].find(
                {"userId": user_id},  # Challenge submissions store userId as string, not ObjectId
                {
                    "challengeId": 1,
                    "video": 1,  # New nested video structure
                    "analysis": 1,
                    "timestamps": 1,
                    "metadata": 1,
                    "userProfile": 1
                }
            ).sort("timestamps.submittedAt", -1).skip(skip if activity_type == 'challenge' else 0).limit(limit if activity_type == 'challenge' else limit).to_list(length=limit)
            
            # Get challenge details for each submission
            for challenge_submission in challenges:
                challenge_id = challenge_submission.get('challengeId')
                if challenge_id:
                    challenge = await db[challenges_collection].find_one({"_id": ObjectId(challenge_id)})
                    if challenge:
                        # Convert ObjectId to string to avoid serialization issues
                        challenge['_id'] = str(challenge['_id'])
                        challenge_submission['challenge'] = challenge
                
                challenge_submission['_id'] = str(challenge_submission['_id'])
                challenge_submission['activityType'] = 'challenge'
                challenge_submission['activityTitle'] = challenge_submission.get('challenge', {}).get('title', 'Challenge Submission')
                
                # Extract video URL from nested video object
                video_data = challenge_submission.get('video', {})
                video_url = video_data.get('url', '')
                thumbnail_url = video_data.get('thumbnail_url', '')
                
                # Get score from analysis
                analysis = challenge_submission.get('analysis', {})
                score = analysis.get('score', 0)
                
                challenge_submission['activitySubtitle'] = f"Score: {score} • {video_data.get('duration', 0)}s"
                challenge_submission['timestamp'] = challenge_submission.get('timestamps', {}).get('submittedAt')
                challenge_submission['previewImage'] = thumbnail_url or video_url
                
                # Ensure challengeId is also converted to string
                if 'challengeId' in challenge_submission:
                    challenge_submission['challengeId'] = str(challenge_submission['challengeId'])
                
                # Add video URLs to the response
                challenge_submission['videoUrl'] = video_url
                challenge_submission['thumbnailUrl'] = thumbnail_url
                
                challenge_submission['metadata'] = {
                    "score": score,
                    "duration": video_data.get('duration', 0),
                    "calories": 0,  # Challenges don't track calories separately
                    "challengeTitle": challenge_submission.get('challenge', {}).get('title', 'Challenge'),
                    "challengeType": challenge_submission.get('challenge', {}).get('type', 'freestyle'),
                    "points": challenge_submission.get('challenge', {}).get('points', 0),
                    "videoUrl": video_url,
                    "thumbnailUrl": thumbnail_url
                }
                all_activities.append(challenge_submission)
        
        # 3. Get Dance Breakdowns
        if not activity_type or activity_type in ['breakdown', 'all']:
            breakdowns = await db[dance_breakdowns_collection].find(
                {"userId": ObjectId(user_id), "success": True},
                {
                    "videoUrl": 1,
                    "playableVideoUrl": 1,
                    "title": 1,
                    "duration": 1,
                    "difficultyLevel": 1,
                    "totalSteps": 1,
                    "createdAt": 1
                }
            ).sort("createdAt", -1).skip(skip if activity_type == 'breakdown' else 0).limit(limit if activity_type == 'breakdown' else limit).to_list(length=limit)
            
            for breakdown in breakdowns:
                breakdown['_id'] = str(breakdown['_id'])
                breakdown['activityType'] = 'breakdown'
                breakdown['activityTitle'] = breakdown.get('title', 'Dance Video Analysis')
                breakdown['activitySubtitle'] = f"{breakdown.get('totalSteps', 0)} steps • {breakdown.get('difficultyLevel', 'Unknown')}"
                breakdown['timestamp'] = breakdown.get('createdAt')
                breakdown['previewImage'] = breakdown.get('playableVideoUrl') or breakdown.get('videoUrl', '')
                
                # Ensure userId is converted to string if it's an ObjectId
                if 'userId' in breakdown and isinstance(breakdown['userId'], ObjectId):
                    breakdown['userId'] = str(breakdown['userId'])
                
                # Add video URLs to the response
                breakdown['videoUrl'] = breakdown.get('videoUrl', '')
                breakdown['playableVideoUrl'] = breakdown.get('playableVideoUrl', '')
                
                breakdown['metadata'] = {
                    "totalSteps": breakdown.get('totalSteps', 0),
                    "duration": breakdown.get('duration', 0),
                    "difficulty": breakdown.get('difficultyLevel', 'Unknown'),
                    "originalUrl": breakdown.get('videoUrl', ''),
                    "playableUrl": breakdown.get('playableVideoUrl', '')
                }
                all_activities.append(breakdown)
        
        # Sort all activities by timestamp (newest first)
        def safe_timestamp(activity):
            timestamp = activity.get('timestamp')
            if timestamp is None:
                return datetime.min
            return timestamp
        
        all_activities.sort(key=safe_timestamp, reverse=True)
        
        # Apply pagination for 'all' type
        if activity_type == 'all':
            start_idx = skip
            end_idx = start_idx + limit
            all_activities = all_activities[start_idx:end_idx]
        
        # Calculate pagination info
        total_count = {
            'all': total_activities,
            'session': sessions_count,
            'challenge': challenges_count,
            'breakdown': breakdowns_count
        }
        
        current_count = len(all_activities)
        has_more = current_count == limit and (skip + limit) < total_count.get(activity_type or 'all', 0)
        
        return {
            "activities": all_activities,
            "total": total_count.get(activity_type or 'all', 0),
            "page": page,
            "limit": limit,
            "hasMore": has_more,
            "summary": {
                "sessions": sessions_count,
                "challenges": challenges_count,
                "breakdowns": breakdowns_count,
                "total": total_activities
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in get_user_history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user history") 

@user_router.get('/api/user/activity-counts', response_model=Dict)
async def get_activity_counts(user_id: str = Depends(get_current_user_id)):
    """
    Get activity counts for each section (for summary cards)
    Returns counts for All, Activities, Breakdowns, Challenges
    """
    try:
        db = Database.get_database()
        
        # Get counts for each section
        sessions_count = await db[dance_sessions_collection].count_documents({"userId": ObjectId(user_id)})
        challenges_count = await db[challenge_submissions_collection].count_documents({"userId": user_id})
        breakdowns_count = await db[dance_breakdowns_collection].count_documents({"userId": ObjectId(user_id), "success": True})
        total_activities = sessions_count + challenges_count + breakdowns_count
        
        return {
            "all": total_activities,
            "activities": sessions_count,  # Sessions are considered "activities"
            "breakdowns": breakdowns_count,
            "challenges": challenges_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error in get_activity_counts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity counts") 