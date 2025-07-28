from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.auth.service import auth_router
from services.user.service import user_router, stats_router
from services.feed.service import feed_router
from services.challenge.service import challenge_router
from services.background.router import background_router
from services.challenge.submission import submission_router
from services.session.service import session_router
from services.ai.service import ai_router
from services.s3.router import s3_router
from infra.mongo import connect_to_mongo, close_mongo_connection

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
        # Add production domains when ready
        # "https://yourdomain.com",
        # "https://www.yourdomain.com",
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
app.include_router(session_router)
app.include_router(ai_router)
app.include_router(s3_router)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
def root():
    return {"message": "Welcome to iDance API Gateway"}

@app.get("/health")
def health():
    return {"status": "ok"} 