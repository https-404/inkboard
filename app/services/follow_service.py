import uuid
from typing import List, Optional
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.models.follow import Follow
from app.db.models.user import User
from app.schemas.follow import (
    FollowResponse,
    FollowersListResponse,
    FollowingListResponse,
    FollowStatusResponse,
    UserBasicInfo,
)
from app.services.minio_service import get_storage_url


class FollowService:
    """Service for handling follow operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _format_user_basic_info(self, user: User) -> UserBasicInfo:
        """Format user as basic info for follow lists."""
        fullname = None
        if user.first_name or user.last_name:
            fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
        
        pfp_url = None
        if user.pfp:
            pfp_url = get_storage_url(user.pfp)
        
        return UserBasicInfo(
            id=str(user.id),
            username=user.username,
            fullname=fullname,
            pfp=pfp_url,
            bio=user.bio,
        )

    async def follow_user(self, follower_id: str, following_id: str) -> FollowResponse:
        """Follow a user."""
        # Prevent self-follow
        if follower_id == following_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot follow yourself",
            )
        
        # Check if target user exists
        user_stmt = select(User).where(User.id == uuid.UUID(following_id))
        user_result = await self.db.execute(user_stmt)
        target_user = user_result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Check if already following
        follow_stmt = select(Follow).where(
            Follow.follower_id == uuid.UUID(follower_id),
            Follow.following_id == uuid.UUID(following_id),
        )
        follow_result = await self.db.execute(follow_stmt)
        existing_follow = follow_result.scalar_one_or_none()
        
        if existing_follow:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already following this user",
            )
        
        # Create follow relationship
        follow = Follow(
            follower_id=uuid.UUID(follower_id),
            following_id=uuid.UUID(following_id),
        )
        self.db.add(follow)
        await self.db.commit()
        
        return FollowResponse(
            follower_id=follower_id,
            following_id=following_id,
            message="Successfully followed user",
            following=True,
        )

    async def unfollow_user(self, follower_id: str, following_id: str) -> FollowResponse:
        """Unfollow a user."""
        # Find follow relationship
        stmt = select(Follow).where(
            Follow.follower_id == uuid.UUID(follower_id),
            Follow.following_id == uuid.UUID(following_id),
        )
        result = await self.db.execute(stmt)
        follow = result.scalar_one_or_none()
        
        if not follow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not following this user",
            )
        
        await self.db.delete(follow)
        await self.db.commit()
        
        return FollowResponse(
            follower_id=follower_id,
            following_id=following_id,
            message="Successfully unfollowed user",
            following=False,
        )

    async def get_follow_status(
        self, follower_id: str, following_id: str
    ) -> FollowStatusResponse:
        """Check if a user is following another user."""
        stmt = select(Follow).where(
            Follow.follower_id == uuid.UUID(follower_id),
            Follow.following_id == uuid.UUID(following_id),
        )
        result = await self.db.execute(stmt)
        follow = result.scalar_one_or_none()
        
        return FollowStatusResponse(
            is_following=follow is not None,
            follower_id=follower_id,
            following_id=following_id,
        )

    async def get_followers(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> FollowersListResponse:
        """Get list of users who follow a given user."""
        # Get followers with user details
        stmt = (
            select(User, Follow)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == uuid.UUID(user_id))
            .order_by(Follow.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # Get total count
        count_stmt = select(func.count(Follow.id)).where(
            Follow.following_id == uuid.UUID(user_id)
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()
        
        followers = [self._format_user_basic_info(user) for user, _ in rows]
        
        return FollowersListResponse(
            user_id=user_id,
            followers=followers,
            total=total,
        )

    async def get_following(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> FollowingListResponse:
        """Get list of users that a given user is following."""
        # Get following with user details
        stmt = (
            select(User, Follow)
            .join(Follow, Follow.following_id == User.id)
            .where(Follow.follower_id == uuid.UUID(user_id))
            .order_by(Follow.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # Get total count
        count_stmt = select(func.count(Follow.id)).where(
            Follow.follower_id == uuid.UUID(user_id)
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()
        
        following = [self._format_user_basic_info(user) for user, _ in rows]
        
        return FollowingListResponse(
            user_id=user_id,
            following=following,
            total=total,
        )

