from fastapi import Depends, Request, HTTPException, status
from typing import Optional

def get_current_user_id(request: Request) -> str:
    payload = getattr(request.state, "user", None)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return payload.get("sub")


def get_optional_user_id(request: Request) -> Optional[str]:
    """Optional authentication - returns None if not authenticated."""
    payload = getattr(request.state, "user", None)
    if not payload:
        return None
    return payload.get("sub")
