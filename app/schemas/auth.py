from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, constr
import uuid


# -------- Base --------
class UserBase(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')

class BaseResponse(BaseModel):
    message: str
    success: bool = True

# -------- Requests --------
class SignupRequest(UserBase):
    password: constr(min_length=8, max_length=72)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh JWT")

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: constr(min_length=6, max_length=6, pattern=r'^\d{6}$')

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    otp: constr(min_length=6, max_length=6, pattern=r'^\d{6}$')
    new_password: constr(min_length=8, max_length=72)

class RefreshRequest(BaseModel):
    refresh_token: str

# -------- Responses --------
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserOut(UserBase):
    id: uuid.UUID
    role: str
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class SignupResponse(BaseResponse): pass
class LoginResponse(TokenPair): pass
class VerifyEmailResponse(BaseResponse): pass
class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
