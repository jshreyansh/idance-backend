from fastapi import APIRouter

feed_router = APIRouter()
 
@feed_router.get('/feed/health')
def feed_health():
    return {"status": "feed service ok"} 