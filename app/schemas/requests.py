from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, Field, StringConstraints

class UserBase(BaseModel):
    """Base user data used in requests"""
    email: EmailStr
    username: Annotated[str, StringConstraints(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')]

class SignupRequest(UserBase):
    """Request payload for user signup"""
    password: Annotated[str, StringConstraints(min_length=8, max_length=72)]

class LoginRequest(BaseModel):
    """Request payload for user login"""
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    """Request payload for token refresh"""
    refresh_token: str = Field(..., description="Valid refresh JWT")

class VerifyEmailRequest(BaseModel):
    """Request payload for email verification"""
    code: str = Field(..., min_length=4, max_length=8)

class RequestPasswordResetRequest(BaseModel):
    """Request payload to start password reset"""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Request payload for password reset"""
    code: str = Field(..., min_length=4, max_length=8)
    new_password: Annotated[str, StringConstraints(min_length=8, max_length=72)]
    confirm_password: str