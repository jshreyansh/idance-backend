from pydantic import BaseModel, EmailStr
from typing import Optional

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleSignInRequest(BaseModel):
    idToken: str
    accessToken: str 