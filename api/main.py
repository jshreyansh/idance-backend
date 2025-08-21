from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.auth.service import auth_router
from services.user.service import user_router, stats_router
from services.feed.service import feed_router
from services.challenge.service import challenge_router
from services.background.router import background_router
from services.challenge.submission import submission_router
from services.challenge.practice_router import practice_router
from services.session.service import session_router
from services.ai.service import ai_router
from services.s3.router import s3_router
from services.rate_limiting.admin import rate_limit_admin_router
from services.rate_limiting.decorators import public_rate_limit
from infra.mongo import connect_to_mongo, close_mongo_connection
from fastapi import Request

app = FastAPI()

# Add CORS middleware for mobile web compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Expo web dev server
        "http://127.0.0.1:3000",
        "http://localhost:8081",  # Alternative Expo port
        "http://127.0.0.1:8081",
        "http://localhost:19006", # Another common Expo web port
        "http://127.0.0.1:19006",
        "http://localhost:19000", # Expo CLI default web port
        "http://127.0.0.1:19000",
        "http://localhost:8080",  # Additional common ports
        "http://127.0.0.1:8080",
        "http://localhost:8000",  # Backend port
        "http://127.0.0.1:8000",
        # Production domains
        "https://androidbuild.d27rf5148zvtld.amplifyapp.com",
        "https://movesai.club",
        "https://www.movesai.club",
        "https://dansync.xyz",        # ✅ Add this
        "https://www.dansync.xyz", 
        # Add more production domains as needed
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(stats_router)
app.include_router(feed_router)
app.include_router(challenge_router)
app.include_router(background_router)
app.include_router(submission_router)
app.include_router(practice_router)
app.include_router(session_router)
app.include_router(ai_router)
app.include_router(s3_router)
app.include_router(rate_limit_admin_router)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
@public_rate_limit('public_data')
async def root(request: Request):
    return {"message": "Welcome to iDance API Gateway"}

@app.get("/health")
@public_rate_limit('health_check')
async def health(request: Request):
    return {"status": "ok"} 