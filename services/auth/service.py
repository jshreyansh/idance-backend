from fastapi import APIRouter, HTTPException
from services.auth.models import SignupRequest, LoginRequest
from services.auth.utils import hash_password, verify_password, create_access_token
from infra.mongo import Database
from datetime import datetime
from bson import ObjectId

auth_router = APIRouter()

@auth_router.post('/auth/signup')
async def signup(data: SignupRequest):
    db = Database.get_database()
    if await db['users'].find_one({'auth.email': data.email}):
        raise HTTPException(status_code=400, detail='Email already registered')
    hashed = hash_password(data.password)
    now = datetime.utcnow()
    user_doc = {
        "auth": {
            "provider": "email",
            "providerId": None,
            "email": data.email,
            "phone": None,
            "passwordHash": hashed,
            "emailVerified": False,
            "phoneVerified": False
        },
        "createdAt": now,
        "lastLoginAt": now
        # All other fields can be added later
    }
    result = await db['users'].insert_one(user_doc)
    user_id = str(result.inserted_id)
    token = create_access_token({"user_id": user_id, "email": data.email})
    return {'message': 'Signup successful', 'user_id': user_id, 'access_token': token, 'token_type': 'bearer'}

@auth_router.post('/auth/login')
async def login(data: LoginRequest):
    db = Database.get_database()
    user = await db['users'].find_one({'auth.email': data.email})
    if not user or not verify_password(data.password, user['auth']['passwordHash']):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    user_id = str(user['_id'])
    token = create_access_token({"user_id": user_id, "email": user['auth']['email']})
    return {"access_token": token, "token_type": "bearer", "user_id": user_id} 