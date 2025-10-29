from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.schemas.search import SearchUserItem, SearchUsersResponse
from app.services.minio_service import get_storage_url


class SearchService:
    """Service for handling search operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_users_by_username(
        self, query: str, limit: int = 10
    ) -> SearchUsersResponse:
        """
        Search users by username (case-insensitive partial match).
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            SearchUsersResponse with results and metadata
        """
        # Case-insensitive search using ILIKE for PostgreSQL
        search_pattern = f"%{query}%"
        
        # Get total count
        count_stmt = (
            select(func.count(User.id))
            .where(User.username.ilike(search_pattern))
            .where(User.is_active == True)
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()
        
        # Get users with limit
        stmt = (
            select(User)
            .where(User.username.ilike(search_pattern))
            .where(User.is_active == True)  # Only return active users
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        # Convert to response format
        results = []
        for user in users:
            fullname = None
            if user.first_name or user.last_name:
                fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
            else:
                fullname = user.username
            
            # Build pfp URL if exists
            pfp_url = None
            if user.pfp:
                pfp_url = get_storage_url(user.pfp)
            
            results.append(
                SearchUserItem(
                    userid=str(user.id),
                    fullname=fullname,
                    bio=user.bio,
                    pfp=pfp_url,
                    username=user.username,
                    email=user.email,
                )
            )
        
        return SearchUsersResponse(
            results=results,
            total=total,
            query=query,
            limit=limit,
        )

