import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.models.user import User
from app.schemas.profile import GetUserProfileResponse, UpdateProfileRequest
from app.services.minio_service import upload_pfp, delete_file, get_storage_url


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID."""
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def get_user_profile(self, user_id: str) -> GetUserProfileResponse:
        """Get user profile with formatted data."""
        user = await self.get_user_by_id(user_id)
        
        fullname = None
        if user.first_name or user.last_name:
            fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
        else:
            fullname = user.username
        
        # Build pfp URL if exists
        pfp_url = None
        if user.pfp:
            pfp_url = get_storage_url(user.pfp)
        
        return GetUserProfileResponse(
            userid=str(user.id),
            fullname=fullname,
            bio=user.bio,
            pfp=pfp_url,
            username=user.username,
            email=user.email,
        )

    async def update_user_profile(
        self,
        user_id: str,
        update_data: UpdateProfileRequest,
        pfp_file=None,
    ) -> GetUserProfileResponse:
        """Update user profile with optional profile picture."""
        user = await self.get_user_by_id(user_id)
        
        # Prepare update dictionary
        update_dict = {}
        
        if update_data.first_name is not None:
            update_dict["first_name"] = update_data.first_name
        if update_data.last_name is not None:
            update_dict["last_name"] = update_data.last_name
        if update_data.bio is not None:
            update_dict["bio"] = update_data.bio
        
        # Handle profile picture upload
        if pfp_file:
            # Delete old pfp if exists
            if user.pfp:
                await delete_file(user.pfp)
            
            # Upload new pfp
            pfp_path = await upload_pfp(pfp_file, str(user.id))
            update_dict["pfp"] = pfp_path
        
        # Update user if there's anything to update
        if update_dict:
            stmt = (
                update(User)
                .where(User.id == user.id)
                .values(**update_dict)
            )
            await self.db.execute(stmt)
            await self.db.commit()
        
        # Return updated profile
        return await self.get_user_profile(user_id)
