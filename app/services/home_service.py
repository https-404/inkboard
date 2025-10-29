import uuid
from typing import List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.article import Article, Clap
from app.db.models.follow import Follow
from app.db.models.user import User
from app.schemas.article import ArticleListItemResponse, AuthorResponse, TagResponse
from app.schemas.follow import UserBasicInfo
from app.services.minio_service import get_storage_url


class HomeService:
    """Service for home feed and user suggestions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _format_author_response(self, user: User) -> AuthorResponse:
        """Format user as author response."""
        fullname = None
        if user.first_name or user.last_name:
            fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
        
        pfp_url = None
        if user.pfp:
            pfp_url = get_storage_url(user.pfp)
        
        return AuthorResponse(
            id=str(user.id),
            username=user.username,
            fullname=fullname,
            pfp=pfp_url,
        )

    async def get_home_feed(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> List[ArticleListItemResponse]:
        """
        Get home feed - latest articles from users that the current user follows.
        """
        # Get list of user IDs that the current user follows
        following_stmt = select(Follow.following_id).where(
            Follow.follower_id == uuid.UUID(user_id)
        )
        following_result = await self.db.execute(following_stmt)
        following_ids = [row[0] for row in following_result.all()]
        
        # If user doesn't follow anyone, return empty list or popular articles
        if not following_ids:
            # Return popular/published articles instead
            stmt = (
                select(Article)
                .join(User, Article.author_id == User.id)
                .options(
                    selectinload(Article.author),
                    selectinload(Article.tags)
                )
                .where(
                    Article.status == "published",
                    Article.published_at.is_not(None)
                )
                .order_by(
                    func.coalesce(Article.published_at, Article.created_at).desc()
                )
                .limit(limit)
                .offset(offset)
            )
        else:
            # Get articles from followed users
            stmt = (
                select(Article)
                .join(User, Article.author_id == User.id)
                .options(
                    selectinload(Article.author),
                    selectinload(Article.tags)
                )
                .where(
                    Article.author_id.in_(following_ids),
                    Article.status == "published",
                    Article.published_at.is_not(None)
                )
                .order_by(
                    func.coalesce(Article.published_at, Article.created_at).desc()
                )
                .limit(limit)
                .offset(offset)
            )
        
        result = await self.db.execute(stmt)
        articles = result.unique().scalars().all()
        
        # Get clap counts for all articles
        clap_map = {}
        if articles:
            article_ids = [str(a.id) for a in articles]
            clap_stmt = (
                select(Clap.article_id, func.sum(Clap.count).label("total_claps"))
                .where(Clap.article_id.in_([uuid.UUID(id) for id in article_ids]))
                .group_by(Clap.article_id)
            )
            clap_result = await self.db.execute(clap_stmt)
            clap_map = {str(row.article_id): row.total_claps for row in clap_result.all()}
        
        responses = []
        for article in articles:
            author = article.author
            clap_count = clap_map.get(str(article.id), 0)
            
            responses.append(
                ArticleListItemResponse(
                    id=str(article.id),
                    title=article.title,
                    subtitle=article.subtitle,
                    slug=article.slug,
                    featured_image=article.featured_image,
                    author=self._format_author_response(author),
                    reading_time=article.reading_time,
                    clap_count=clap_count,
                    tags=[TagResponse(id=str(t.id), name=t.name, slug=t.slug, description=t.description) for t in article.tags],
                    status=article.status,
                    published_at=article.published_at,
                    created_at=article.created_at,
                    updated_at=article.updated_at,
                )
            )
        
        return responses

    def _format_user_basic_info(self, user: User) -> UserBasicInfo:
        """Format user as basic info for suggestions."""
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

    async def suggest_users(
        self, user_id: str, limit: int = 10
    ) -> List[UserBasicInfo]:
        """
        Suggest users to follow.
        
        Strategy:
        1. Exclude users already followed
        2. Exclude self
        3. Prioritize users with most followers (popular)
        4. Optionally suggest users with mutual connections
        """
        # Get users already followed
        following_stmt = select(Follow.following_id).where(
            Follow.follower_id == uuid.UUID(user_id)
        )
        following_result = await self.db.execute(following_stmt)
        following_ids = {row[0] for row in following_result.all()}
        
        # Build query - users with most followers, excluding self and already followed
        subquery = (
            select(
                Follow.following_id,
                func.count(Follow.follower_id).label("follower_count")
            )
            .group_by(Follow.following_id)
            .subquery()
        )
        
        stmt = (
            select(User, func.coalesce(subquery.c.follower_count, 0).label("follower_count"))
            .outerjoin(subquery, User.id == subquery.c.following_id)
            .where(
                User.id != uuid.UUID(user_id),  # Exclude self
                User.is_active == True,  # Only active users
                User.id.notin_(following_ids) if following_ids else True  # Exclude already followed
            )
            .order_by(subquery.c.follower_count.desc(), User.created_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        suggestions = []
        for user, _ in rows:
            suggestions.append(self._format_user_basic_info(user))
        
        return suggestions

    async def get_trending_articles(
        self, limit: int = 20, offset: int = 0
    ) -> List[ArticleListItemResponse]:
        """
        Get trending articles based on claps and recency.
        """
        # Get articles with clap counts, ordered by claps and recency
        stmt = (
            select(
                Article,
                func.coalesce(func.sum(Clap.count), 0).label("total_claps")
            )
            .outerjoin(Clap, Article.id == Clap.article_id)
            .join(User, Article.author_id == User.id)
            .options(
                selectinload(Article.author),
                selectinload(Article.tags)
            )
            .where(
                Article.status == "published",
                Article.published_at.is_not(None)
            )
            .group_by(Article.id)
            .order_by(
                func.coalesce(func.sum(Clap.count), 0).desc(),
                func.coalesce(Article.published_at, Article.created_at).desc()
            )
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        responses = []
        for article, clap_count in rows:
            author = article.author
            
            responses.append(
                ArticleListItemResponse(
                    id=str(article.id),
                    title=article.title,
                    subtitle=article.subtitle,
                    slug=article.slug,
                    featured_image=article.featured_image,
                    author=self._format_author_response(author),
                    reading_time=article.reading当中,
                    clap_count=int(clap_count) if clap_count else 0,
                    tags=[TagResponse(id=str(t.id), name=t.name, slug=t.slug, description=t.description) for t in article.tags],
                    status=article.status,
                    published_at=article.published_at,
                    created_at=article.created_at,
                    updated_at=article.updated_at,
                )
            )
        
        return responses

