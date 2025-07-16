from fastapi import APIRouter, Depends, HTTPException, status, Header
from services.user.models import UserProfileUpdate
from infra.mongo import Database
from datetime import datetime
from jose import jwt, JWTError
from bson import ObjectId

JWT_SECRET = "supersecretkey123"
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