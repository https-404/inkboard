from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional
from app.api.deps.auth import get_current_user_id
from app.core.deps import get_db
from app.services.user_service import UserService
from app.schemas.profile import UpdateProfileRequest, GetUserProfileResponse
from app.core.deps import AsyncSession

user_router = APIRouter(prefix="/users", tags=["User"])


@user_router.get("/me", response_model=GetUserProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile."""
    user_service = UserService(db)
    return await user_service.get_user_profile(user_id)


@user_router.post("/me", response_model=GetUserProfileResponse)
async def create_or_update_profile(
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    pfp: Optional[UploadFile] = File(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create or update user profile.
    Accepts form data with optional profile picture upload.
    """
    user_service = UserService(db)
    update_data = UpdateProfileRequest(
        first_name=first_name,
        last_name=last_name,
        bio=bio,
    )
    return await user_service.update_user_profile(
        user_id=user_id,
        update_data=update_data,
        pfp_file=pfp,
    )


@user_router.put("/me", response_model=GetUserProfileResponse)
async def update_profile(
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    pfp: Optional[UploadFile] = File(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user profile.
    Accepts form data with optional profile picture upload.
    """
    user_service = UserService(db)
    update_data = UpdateProfileRequest(
        first_name=first_name,
        last_name=last_name,
        bio=bio,
    )
    return await user_service.update_user_profile(
        user_id=user_id,
        update_data=update_data,
        pfp_file=pfp,
    )
