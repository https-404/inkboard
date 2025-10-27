from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class MessageResponse(BaseModel):
    """Base response with message and success status"""
    message: str
    success: bool = True

class TokenResponse(BaseModel):
    """Base token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginResponse(TokenResponse):
    """Response for successful login"""
    pass

class RefreshTokenResponse(BaseModel):
    """Response for token refresh"""
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    """User data response"""
    email: str
    username: str
    role: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

class SignupResponse(MessageResponse):
    """Response for successful signup"""
    pass

class VerifyEmailResponse(MessageResponse):
    """Response for email verification"""
    pass

class RequestPasswordResetResponse(MessageResponse):
    """Response for password reset request"""
    pass

class ResetPasswordResponse(MessageResponse):
    """Response for password reset completion"""
    pass

class LogoutResponse(MessageResponse):
    """Response for successful logout"""
    pass