from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.services.search_service import SearchService
from app.schemas.search import SearchUsersResponse

search_router = APIRouter(prefix="/search", tags=["Search"])


@search_router.get("/users", response_model=SearchUsersResponse)
async def search_users_by_username(
    q: str = Query(..., min_length=1, description="Search query for username"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search users by username.
    
    Performs a case-insensitive partial match search on username.
    
    Args:
        q: Search query string (minimum 1 character)
        limit: Maximum number of results to return (1-100, default: 10)
        db: Database session
        
    Returns:
        SearchUsersResponse containing results and metadata
    """
    search_service = SearchService(db)
    return await search_service.search_users_by_username(query=q, limit=limit)

