from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.schemas.profile import GetUserProfileResponse

class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_user_profile(self, user_id: str) -> GetUserProfileResponse:
        stmt = (
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.bio,
                User.pfp,
                User.username,
                User.email
            )
            .where(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        user = result.mappings().first()  

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        fullname = None
        if user.get("first_name") or user.get("last_name"):
            fullname = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        else:
            fullname = user.get("username")
        return GetUserProfileResponse(
            userid=str(user["id"]),
            fullname=fullname,
            bio=user.get("bio"),
            pfp=user.get("pfp"),
            username=user.get("username"),
            email=user.get("email"),
        )
