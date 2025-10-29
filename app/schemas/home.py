from typing import List
from pydantic import BaseModel

from app.schemas.article import ArticleListItemResponse
from app.schemas.search import UserBasicInfo


#---------------- RESPONSES -----------------------------------
class HomeFeedResponse(BaseModel):
    """Response for home feed."""
    articles: List[ArticleListItemResponse] = []
    total: int = 0


class TrendingArticlesResponse(BaseModel):
    """Response for trending articles."""
    articles: List[ArticleListItemResponse] = []
    total: int = 0


class UserSuggestionsResponse(BaseModel):
    """Response for user suggestions."""
    suggestions: List[UserBasicInfo] = []
    total: int = 0

