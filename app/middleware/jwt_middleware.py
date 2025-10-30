from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status
from app.core.security import decode_token
import logging

logger = logging.getLogger("jwt_middleware")


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates JWTs from Authorization header
    and attaches the decoded user to request.state.user
    """

    def __init__(self, app, exempt_paths: list[str] | None = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/api/v1/auth/",
            "/api/v1/inkboard/storage/",
            "/api/v1/home/trending",  # Trending articles is public
            "/docs",
            "/openapi.json",
            "/favicon.ico"
            "/redoc",
        ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(ex) for ex in self.exempt_paths):
            return await call_next(request)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header.split(" ", 1)[1].strip()

        try:
            payload = decode_token(token)
            if not payload:
                raise ValueError("Invalid token")

            request.state.user = payload
            logger.debug(f"Authenticated request for user={payload.get('sub')}")
        except Exception as e:
            logger.warning(f"JWT validation failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
            )
        return await call_next(request)
