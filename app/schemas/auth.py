from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserOut(UserBase):
    """User response payload (public-safe)."""
    id: int
    role: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SignupRequest(BaseModel):
    email: EmailStr = Field(..., example="john@example.com")
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh JWT")


class OTPVerifyRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=8)
    purpose: str = Field(..., description="Purpose of OTP e.g. 'verify_email' or 'reset_password'")

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    user: UserOut
    tokens: TokenPair


class SignupResponse(BaseModel):
    user: UserOut
    message: str = "Signup successful, please verify your email"


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
