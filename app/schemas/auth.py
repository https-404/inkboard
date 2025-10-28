from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, Field, StringConstraints, ConfigDict
import uuid

# -------- Base --------
class UserBase(BaseModel):
    email: EmailStr
    username: Annotated[str, StringConstraints(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')]

class BaseResponse(BaseModel):
    message: str
    success: bool = True

# -------- Requests --------
class SignupRequest(UserBase):
    password: Annotated[str, StringConstraints(min_length=8, max_length=72)]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh JWT")

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: Annotated[str, StringConstraints(min_length=6, max_length=6, pattern=r'^\d{6}$')]

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    otp: Annotated[str, StringConstraints(min_length=6, max_length=6, pattern=r'^\d{6}$')]
    new_password: Annotated[str, StringConstraints(min_length=8, max_length=72)]

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

    model_config = ConfigDict(from_attributes=True)

class SignupResponse(BaseResponse): pass
class LoginResponse(TokenPair): pass
class VerifyEmailResponse(BaseResponse): pass
class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
class ForgotPasswordResponse(BaseResponse): pass
class ResetPasswordResponse(BaseResponse): pass
class ResendVerificationEmailResponse(BaseResponse): pass
class VerifyOTPResponse(BaseResponse): pass
class SendVerificationEmailResponse(BaseResponse): pass
