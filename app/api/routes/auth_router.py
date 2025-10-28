from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.deps import get_db
from app.schemas.auth import (
    ForgotPasswordRequest, LoginResponse, ResetPasswordRequest, UserOut, SignupRequest,
    LoginRequest, SignupResponse, RefreshRequest,
    RefreshResponse, VerifyEmailRequest, VerifyEmailResponse
)
from app.services.auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/signup",
    summary="User Signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED
)
async def signup(
    req: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user account.
    
    Args:
        req: User signup information including email, username, and password
        db: Database session
        
    Returns:
        Created user information (excluding password)
        
    Raises:
        HTTPException: If email/username already exists or other validation errors
    """
    try:
        service = AuthService(db)
        return await service.signup(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@auth_router.post(
    "/login",
    summary="User Login",
    response_model=LoginResponse,
)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return access and refresh tokens.
    
    Args:
        req: User login information including email and password
        db: Database session

    Returns:
        Access and refresh tokens for the authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    try:
        service = AuthService(db)
        return await service.login(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@auth_router.post(
    "/refresh",
    summary="Refresh Access Token",
    response_model=RefreshResponse
)
async def refresh_token(
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    """
    Refresh access token using a valid refresh token.
    
    Args:
        req: The refresh token request containing a valid refresh JWT
        db: Database session
        
    Returns:
        A new access token
        
    Raises:
        HTTPException: If refresh token is invalid, expired, or revoked
    """
    service = AuthService(db)
    return await service.refresh(req)


@auth_router.post(
    "/verify-email",
    summary="Verify Email Address",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK
)
async def verify_email(
    req: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyEmailResponse:
    """
    Verify user's email address using the OTP sent during signup.

    Args:
        req: Email verification request containing email and OTP
        db: Database session

    Returns:
        VerifyEmailResponse: Success message if verification is successful

    Raises:
        HTTPException: If OTP is invalid or expired
    """
    auth_service = AuthService(db)
    await auth_service.verify_email(req.email, req.otp)
    
    return VerifyEmailResponse(
        message="Email verified successfully",
        success=True
    )

@auth_router.post(
    "/password/forgot",
    summary="Forgot Password",
    status_code=status.HTTP_200_OK
)
async def send_verification_email(
    req: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend the email verification OTP to the user's email address.

    Args:
        req: Request containing the user's email address
        db: Database session

    Returns:
        Success message if email is sent

    Raises:
        HTTPException: If resending email fails
    """
    auth_service = AuthService(db)
    await auth_service.resend_verification_email(req.email)
    
    return {"message": f"Verification email sent to {req.email}"}

@auth_router.post(
    "/password/verify-otp",
    summary="Verify OTP for Forgot Password",
    status_code=status.HTTP_200_OK
)
async def verify_forgot_password_otp(
    req: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify the OTP sent to the user's email for password reset.

    Args:
        req: Request containing email and OTP
        db: Database session
    Returns:
        Success message if OTP is valid
        """
    auth_service = AuthService(db)
    return await auth_service.verify_otp(req.email, req.otp)
    
@auth_router.post(
    "/password/reset",
    summary="Reset Password",
    status_code=status.HTTP_200_OK
)
async def reset_password(
    req: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset the user's password using the provided OTP and new password.

    Args:
        req: Request containing OTP and new password
        db: Database session

    Returns:
        Success message if password is reset

    Raises:
        HTTPException: If OTP is invalid or password reset fails
    """
    auth_service = AuthService(db)
    await auth_service.reset_password(req.otp, req.new_password)
    
    return {"message": "Password has been reset successfully"}
