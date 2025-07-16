from fastapi import APIRouter

ai_router = APIRouter()
 
@ai_router.get('/ai/health')
def ai_health():
    return {"status": "ai service ok"} 