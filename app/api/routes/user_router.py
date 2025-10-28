from fastapi import APIRouter, Depends
from app.api.deps.auth import get_current_user_id
from app.core.deps import get_db
from app.services.user_service import UserService
from app.core.deps import AsyncSession
user_router = APIRouter(prefix="/users", tags=["User"])

@user_router.get("/me")
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    ):
    user_service = UserService(db)
    return await user_service.get_user_profile(user_id)
