from fastapi import FastAPI
from services.auth.service import auth_router
from services.user.service import user_router
from services.feed.service import feed_router
from services.challenge.service import challenge_router
from services.session.service import session_router
from services.ai.service import ai_router
from infra.mongo import connect_to_mongo, close_mongo_connection

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(feed_router)
app.include_router(challenge_router)
app.include_router(session_router)
app.include_router(ai_router)

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