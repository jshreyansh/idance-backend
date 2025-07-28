from fastapi import APIRouter, Depends, HTTPException, status, Header, Body
from services.user.models import UserProfileUpdate, UserStatsUpdateRequest, UserStatsResponse
from infra.mongo import Database
from datetime import datetime
from jose import jwt, JWTError
from bson import ObjectId
from typing import List
from pydantic import BaseModel
import os
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
        return UserStatsResponse()
    stats.pop('_id', None)
    return UserStatsResponse(**stats)

@stats_router.post('/api/stats/update')
async def update_my_stats(
    update: UserStatsUpdateRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    db = Database.get_database()
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
            'mostPlayedStyle': update.style  # Optionally, improve this logic later
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
    from datetime import datetime, timedelta
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
    
    # Calculate calories per day
    calories_per_day = {}
    for session in sessions:
        session_date = session['startTime'].date().strftime('%Y-%m-%d')
        calories = session.get('caloriesBurned', 0) or 0
        calories_per_day[session_date] = calories_per_day.get(session_date, 0) + calories
    
    # Generate last N days with calories data
    result = []
    for i in range(days - 1, -1, -1):  # Reverse order to get oldest to newest
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        sessions_count = activity_map.get(date_str, 0)
        calories_burned = calories_per_day.get(date_str, 0)
        result.append(HeatmapResponse(
            date=date_str,
            sessionsCount=sessions_count,
            isActive=sessions_count > 0,
            caloriesBurned=calories_burned
        ))
    
    return result 