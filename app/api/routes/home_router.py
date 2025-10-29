from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.api.deps.auth import get_current_user_id, get_optional_user_id
from app.services.home_service import HomeService
from app.schemas.home import (
    HomeFeedResponse,
    TrendingArticlesResponse,
    UserSuggestionsResponse,
)

home_router = APIRouter(prefix="/home", tags=["Home"])


@home_router.get("/feed", response_model=HomeFeedResponse)
async def get_home_feed(
    limit: int = Query(20, ge=1, le=100, description="Number of articles"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get home feed - latest articles from users you follow.
    
    If you don't follow anyone, returns popular/published articles instead.
    Requires authentication.
    """
    home_service = HomeService(db)
    articles = await home_service.get_home_feed(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    
    return HomeFeedResponse(
        articles=articles,
        total=len(articles),  # Can be enhanced with proper count query if needed
    )


@home_router.get("/trending", response_model=TrendingArticlesResponse)
async def get_trending_articles(
    limit: int = Query(20, ge=1, le=100, description="Number of articles"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trending articles based on claps and recency.
    
    Public endpoint - no authentication required.
    """
    home_service = HomeService(db)
    articles = await home_service.get_trending_articles(
        limit=limit,
        offset=offset,
    )
    
    return TrendingArticlesResponse(
        articles=articles,
        total=len(articles),
    )


@home_router.get("/suggest-users", response_model=UserSuggestionsResponse)
async def suggest_users(
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user suggestions - users you might want to follow.
    
    Suggests popular users (based on follower count) that you're not already following.
    Requires authentication.
    """
    home_service = HomeService(db)
    suggestions = await home_service.suggest_users(
        user_id=user_id,
        limit=limit,
    )
    
    return UserSuggestionsResponse(
        suggestions=suggestions,
        total=len(suggestions),
    )

