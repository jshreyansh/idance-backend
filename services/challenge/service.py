from fastapi import APIRouter

challenge_router = APIRouter()
 
@challenge_router.get('/challenge/health')
def challenge_health():
    return {"status": "challenge service ok"} 