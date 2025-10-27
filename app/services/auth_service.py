import secrets
import logging
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException, status

from app.db.models.user import User
from app.db.models.token import Token
from app.db.models.otp import OtpCode
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    utc_now,
)
from app.schemas.auth import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    TokenPair,
    RefreshRequest,
    RefreshResponse,
)
from app.schemas.auth import UserOut

logger = logging.getLogger(__name__)
UTC = timezone.utc


class AuthService:
    """
    Handles signup, login, refresh, and OTP with DTO-based input/output.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def refresh_token(self, req: RefreshRequest) -> RefreshResponse:
        """
        Refresh an access token using a valid refresh token.

        Args:
            req: Request containing a valid refresh token

        Returns:
            A new access token

        Raises:
            ValueError: If refresh token is invalid, expired, or has been revoked
        """
        # Decode token without verification first to get the JTI
        try:
            unverified_payload = jwt.decode(
                req.refresh_token,
                options={"verify_signature": False}
            )
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token format: {str(e)}")
            
        if unverified_payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

            # Find the token in the database
            stmt = select(Token).join(User).where(
                and_(
                    Token.jti == unverified_payload.get("jti"),
                    Token.revoked.is_(False),
                    Token.expires_at > utc_now()
                )
            )
            result = await self.db.execute(stmt)
            token_record = result.scalar_one_or_none()

            if not token_record:
                raise ValueError("Token not found or has been revoked")

            # Verify the token signature and claims
            try:
                payload = jwt.decode(
                    req.refresh_token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM]
                )
            except jwt.InvalidTokenError as e:
                await self._revoke_token(token_record.jti)
                raise ValueError(f"Invalid token: {str(e)}")

            # Revoke the old refresh token
            await self._revoke_token(token_record.jti)
            
            # Generate new token pair
            access_token = create_access_token(
                user_id=token_record.user.id,
                email=token_record.user.email,
                username=token_record.user.username,
                role=token_record.user.role,
            )
            
            refresh_token, jti, expires_at = create_refresh_token(
                user_id=token_record.user.id,
                email=token_record.user.email,
                username=token_record.user.username,
                role=token_record.user.role,
            )

            # Store new refresh token
            new_token = Token(
                user_id=token_record.user.id,
                jti=jti,
                token=refresh_token,  # Consider hashing for additional security
                user_agent=token_record.user_agent,  # Preserve the original session info
                ip_address=token_record.ip_address,
                expires_at=expires_at,
            )
            self.db.add(new_token)
            await self.db.commit()

            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )

    async def _revoke_token(self, jti: str) -> None:
        """
        Revoke a refresh token by its JTI.

        Args:
            jti: The unique identifier of the token to revoke
        """
        stmt = (
            update(Token)
            .where(Token.jti == jti)
            .values(
                revoked=True,
                revoked_at=utc_now()
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def signup(self, req: SignupRequest) -> SignupResponse:
        try:
            user = User(
                email=req.email.lower(),
                username=req.username,
                hashed_password=hash_password(req.password),
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"[AuthService] Created user {req.email}")

            return SignupResponse(
                message="Signup successful, please verify your email",
                success=True
            )

        except IntegrityError:
            await self.db.rollback()
            logger.warning(f"[AuthService] Duplicate signup for {req.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already exists.",
            )

        except SQLAlchemyError:
            await self.db.rollback()
            logger.exception("[AuthService] Database error during signup.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during signup.",
            )


    async def login(
        self,
        req: LoginRequest,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LoginResponse:
        try:
            res = await self.db.execute(select(User).where(User.email == req.email.lower()))
            user = res.scalar_one_or_none()

            if not user or not verify_password(req.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password.",
                )

            tokens = await self._issue_token_pair(
                user,
                user_agent=user_agent,
                ip_address=ip_address,
            )

            logger.info(f"[AuthService] Login success for {req.email}")

            return LoginResponse(**tokens)

        except HTTPException:
            raise
        except SQLAlchemyError:
            logger.exception("[AuthService] Database error during login.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during login.",
            )


    async def refresh(self, req: RefreshRequest) -> RefreshResponse:
        """Exchange a valid refresh token for a new access token."""
        from app.core.security import decode_token  # local import avoids circularity

        try:
            payload = decode_token(req.refresh_token)
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token.",
                )

            jti = payload.get("jti")
            if not await self._is_refresh_valid(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token expired or revoked.",
                )

            new_access = create_access_token(
                user_id=payload["sub"],
                email=payload["email"],
                username=payload["username"],
                role=payload["role"],
            )

            logger.info(f"[AuthService] Issued new access token for user={payload['email']}")

            return RefreshResponse(access_token=new_access)

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("[AuthService] Error refreshing token.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh token.",
            )

    async def _issue_token_pair(
        self,
        user: User,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> dict:
        try:
            access_token = create_access_token(
                user_id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
            )
            refresh_token, jti, exp = create_refresh_token(
                user_id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
            )
            db_token = Token(
                user_id=user.id,
                token=refresh_token,
                jti=jti,
                expires_at=exp,
                user_agent=user_agent,
                ip_address=ip_address,
            )
            self.db.add(db_token)
            await self.db.commit()
            await self.db.refresh(db_token)
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        except SQLAlchemyError:
            await self.db.rollback()
            logger.exception("[AuthService] Failed to issue token pair.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to issue tokens.",
            )

    async def _is_refresh_valid(self, jti: str) -> bool:
        try:
            res = await self.db.execute(select(Token).where(Token.jti == jti, Token.revoked == False))
            token = res.scalar_one_or_none()
            return bool(token and token.expires_at > datetime.now(UTC))
        except SQLAlchemyError:
            logger.exception("[AuthService] DB error validating refresh token.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error validating token.",
            )
