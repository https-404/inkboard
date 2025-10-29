from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.api.deps.auth import get_current_user_id
from app.services.follow_service import FollowService
from app.schemas.follow import (
    FollowResponse,
    FollowersListResponse,
    FollowingListResponse,
    FollowStatusResponse,
)

follow_router = APIRouter(prefix="/follows", tags=["Follows"])


@follow_router.post("/{following_id}", response_model=FollowResponse)
async def follow_user(
    following_id: str = Path(..., description="User ID to follow"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Follow a user.
    
    Requires authentication. You cannot follow yourself.
    """
    follow_service = FollowService(db)
    return await follow_service.follow_user(
        follower_id=user_id,
        following_id=following_id,
    )


@follow_router.delete("/{following_id}", response_model=FollowResponse)
async def unfollow_user(
    following_id: str = Path(..., description="User ID to unfollow"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Unfollow a user.
    
    Requires authentication.
    """
    follow_service = FollowService(db)
    return await follow_service.unfollow_user(
        follower_id=user_id,
        following_id=following_id,
    )


@follow_router.get("/status/{following_id}", response_model=FollowStatusResponse)
async def get_follow_status(
    following_id: str = Path(..., description="User ID to check follow status"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if current user is following a specific user.
    
    Requires authentication.
    """
    follow_service = FollowService(db)
    return await follow_service.get_follow_status(
        follower_id=user_id,
        following_id=following_id,
    )


@follow_router.get("/followers/{user_id}", response_model=FollowersListResponse)
async def get_followers(
    user_id: str = Path(..., description="User ID to get followers for"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user_id_auth: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of users who follow a specific user.
    
    Requires authentication for privacy.
    """
    follow_service = FollowService(db)
    return await follow_service.get_followers(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@follow_router.get("/following/{user_id}", response_model=FollowingListResponse)
async def get_following(
    user_id: str = Path(..., description="User ID to get following list for"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user_id_auth: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of users that a specific user is following.
    
    Requires authentication for privacy.
    """
    follow_service = FollowService(db)
    return await follow_service.get_following(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

