from fastapi import APIRouter

session_router = APIRouter()
 
@session_router.get('/session/health')
def session_health():
    return {"status": "session service ok"} 