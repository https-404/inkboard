from fastapi import Depends, Request, HTTPException, status

def get_current_user_id(request: Request) -> str:
    payload = getattr(request.state, "user", None)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return payload.get("sub")
