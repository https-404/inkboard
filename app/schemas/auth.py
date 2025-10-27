from datetime import datetime
import uuid
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, Field, StringConstraints

# Base Models
class UserBase(BaseModel):
    email: EmailStr
    username: str

class BaseResponse(BaseModel):
    """Base response with message and success status"""
    message: str
    success: bool = True

class TokenBase(BaseModel):
    """Base token response"""
    access_token: str
    token_type: str = "bearer"

class TokenPair(TokenBase):
    """Response containing both access and refresh tokens"""
    refresh_token: str

# Request Models
class SignupRequest(BaseModel):
    """Request payload for user signup"""
    email: EmailStr = Field(..., example="john@example.com")
    username: Annotated[str, StringConstraints(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')]
    password: Annotated[str, StringConstraints(min_length=8, max_length=72)]

class LoginRequest(BaseModel):
    """Request payload for user login"""
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    """Request payload for token refresh"""
    refresh_token: str = Field(..., description="Valid refresh JWT")

class OTPVerifyRequest(BaseModel):
    """Request payload for OTP verification"""
    code: str = Field(..., min_length=4, max_length=8)
    purpose: str = Field(..., description="Purpose of OTP e.g. 'verify_email' or 'reset_password'")

# Response Models
class UserOut(UserBase):
    """User response payload (public-safe)"""
    id: uuid.UUID
    role: str
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class SignupResponse(BaseResponse):
    """Response for successful signup"""
    pass

class LoginResponse(TokenPair):
    """Response for successful login - contains only tokens"""
    pass

class RefreshResponse(TokenBase):
    """Response for token refresh - contains only the new access token"""
    pass
