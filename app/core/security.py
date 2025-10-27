from datetime import datetime, timedelta, timezone
import uuid
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def utc_now() -> datetime:
    """Get the current UTC time."""
    return datetime.now(timezone.utc)

def create_access_token(
    user_id: int,
    email: str,
    username: str,
    role: str,
) -> str:
    """
    Create a short-lived access token that carries user identity & role.
    """
    expire = utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "username": username,
        "role": role,
        "type": "access",
        "exp": int(expire.timestamp()),
        "iat": int(utc_now().timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(
    user_id: int,
    email: str,
    username: str,
    role: str,
) -> tuple[str, str, datetime]:
    """
    Create a long-lived refresh token and return (token, jti, expires_at).
    """
    jti = uuid.uuid4().hex
    expire = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "username": username,
        "role": role,
        "type": "refresh",
        "jti": jti,
        "exp": int(expire.timestamp()),
        "iat": int(utc_now().timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti, expire


def decode_token(token: str) -> dict | None:
    """
    Decode and validate a JWT, returning payload or None if invalid.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None