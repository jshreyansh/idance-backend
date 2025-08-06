from fastapi import APIRouter, HTTPException
from services.auth.models import SignupRequest, LoginRequest, GoogleSignInRequest
from services.auth.utils import hash_password, verify_password, create_access_token
from services.auth.google_utils import verify_google_token, fetch_google_profile_data
from infra.mongo import Database
from datetime import datetime
from bson import ObjectId
from typing import Optional

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

@auth_router.post('/auth/google')
async def google_sign_in(data: GoogleSignInRequest):
    """
    Handle Google Sign-In using ID token and access token
    """
    print(f"🔍 Google sign-in attempt received")
    print(f"🔍 ID Token length: {len(data.idToken) if data.idToken else 0}")
    print(f"🔍 Access Token length: {len(data.accessToken) if data.accessToken else 0}")
    
    db = Database.get_database()
    
    try:
        # Verify Google ID token and get basic user info
        print(f"🔍 Attempting to verify Google token...")
        google_user_info = await verify_google_token(data.idToken)
        
        # Fetch extended profile data from Google People API
        profile_data = await fetch_google_profile_data(data.accessToken)
        
        # Check if user already exists
        existing_user = await db['users'].find_one({
            '$or': [
                {'auth.providerId': google_user_info['google_id']},
                {'auth.email': google_user_info['email']}
            ]
        })
        
        now = datetime.utcnow()
        
        if existing_user:
            # Update existing user with latest Google data
            user_id = str(existing_user['_id'])
            
            # Update auth info if it's a Google user or convert email user to Google
            update_fields = {
                "auth.provider": "google",
                "auth.providerId": google_user_info['google_id'],
                "auth.email": google_user_info['email'],
                "auth.emailVerified": google_user_info['email_verified'],
                "lastLoginAt": now
            }
            
            # Update profile info if available
            if google_user_info.get('name'):
                update_fields["profile.displayName"] = google_user_info['name']
            if google_user_info.get('picture'):
                update_fields["profile.avatarUrl"] = google_user_info['picture']
            
            # Add extended profile data if available
            if profile_data:
                if profile_data.get('gender'):
                    update_fields["profile.gender"] = profile_data['gender']
                if profile_data.get('birth_year'):
                    update_fields["profile.birthYear"] = profile_data['birth_year']
                if profile_data.get('phone'):
                    update_fields["auth.phone"] = profile_data['phone']
                    update_fields["auth.phoneVerified"] = True
                if profile_data.get('location'):
                    update_fields["profile.location"] = profile_data['location']
            
            await db['users'].update_one(
                {"_id": existing_user['_id']},
                {"$set": update_fields}
            )
            
        else:
            # Create new user
            user_doc = {
                "auth": {
                    "provider": "google",
                    "providerId": google_user_info['google_id'],
                    "email": google_user_info['email'],
                    "phone": profile_data.get('phone') if profile_data else None,
                    "passwordHash": None,
                    "emailVerified": google_user_info['email_verified'],
                    "phoneVerified": bool(profile_data.get('phone')) if profile_data else False
                },
                "profile": {
                    "username": None,  # User can set this later
                    "displayName": google_user_info.get('name'),
                    "avatarUrl": google_user_info.get('picture'),
                    "bio": None,
                    "gender": profile_data.get('gender') if profile_data else None,
                    "birthYear": profile_data.get('birth_year') if profile_data else None,
                    "location": profile_data.get('location') if profile_data else None
                },
                "createdAt": now,
                "lastLoginAt": now,
                "updatedAt": now
            }
            
            result = await db['users'].insert_one(user_doc)
            user_id = str(result.inserted_id)
        
        # Generate JWT token
        token = create_access_token({
            "user_id": user_id, 
            "email": google_user_info['email']
        })
        
        return {
            "message": "Google sign-in successful",
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id,
            "user": {
                "email": google_user_info['email'],
                "name": google_user_info.get('name'),
                "picture": google_user_info.get('picture'),
                "email_verified": google_user_info['email_verified']
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions from token verification
        raise
    except Exception as e:
        print(f"Google sign-in error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during Google sign-in")

@auth_router.get('/auth/google/test')
async def test_google_config():
    """
    Test endpoint to verify Google OAuth configuration
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_id_web = os.getenv("GOOGLE_CLIENT_ID_WEB")
    jwt_secret = os.getenv("JWT_SECRET", "default")
    
    return {
        "status": "Google OAuth configuration check",
        "google_client_id_configured": bool(google_client_id and google_client_id != "your-google-client-id.apps.googleusercontent.com"),
        "google_client_id_web_configured": bool(google_client_id_web and google_client_id_web != ""),
        "jwt_secret_configured": bool(jwt_secret and jwt_secret != "default"),
        "endpoints_available": [
            "POST /auth/google - Google Sign-In",
            "GET /auth/google/test - Configuration Test",
            "POST /auth/signup - Email Signup", 
            "POST /auth/login - Email Login"
        ]
    } 