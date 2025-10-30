import uuid
import re
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.db.models.article import Article, Tag, ArticleTag, Clap
from app.db.models.user import User
from app.schemas.article import (
    CreateArticleRequest,
    UpdateArticleRequest,
    ArticleDetailResponse,
    ArticleListItemResponse,
    AuthorResponse,
    TagResponse,
    ContentBlock,
)
from app.services.minio_service import get_storage_url


class ArticleService:
    """Service for handling article operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title."""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        return slug[:500]  # Ensure max length

    def _calculate_reading_time(self, content: List[dict]) -> int:
        """Calculate reading time in minutes based on content blocks."""
        word_count = 0
        for block in content:
            if block.get("type") == "paragraph":
                text = block.get("content", "")
                word_count += len(text.split())
            elif block.get("type") == "heading":
                text = block.get("content", "")
                word_count += len(text.split())
            elif block.get("type") == "quote":
                text = block.get("content", "")
                word_count += len(text.split())
            elif block.get("type") == "list":
                items = block.get("content", [])
                for item in items:
                    word_count += len(item.split())
        
        # Average reading speed: 200 words per minute
        reading_time = max(1, (word_count // 200) + (1 if word_count % 200 > 0 else 0))
        return reading_time

    def _content_to_dict(self, content: List[ContentBlock]) -> List[dict]:
        """Convert Pydantic content blocks to dictionaries."""
        result = []
        for block in content:
            block_dict = block.model_dump()
            result.append(block_dict)
        return result

    async def _get_or_create_tags(self, tag_names: List[str]) -> List[Tag]:
        """Get existing tags or create new ones."""
        tags = []
        for tag_name in tag_names:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            
            # Generate slug
            tag_slug = re.sub(r'[^\w\s-]', '', tag_name)
            tag_slug = re.sub(r'[-\s]+', '-', tag_slug).strip('-')
            
            # Check if tag exists
            stmt = select(Tag).where(Tag.slug == tag_slug)
            result = await self.db.execute(stmt)
            tag = result.scalar_one_or_none()
            
            if not tag:
                tag = Tag(name=tag_name, slug=tag_slug)
                self.db.add(tag)
                await self.db.flush()
            
            tags.append(tag)
        
        return tags

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

    async def create_article(
        self, author_id: str, request: CreateArticleRequest
    ) -> ArticleDetailResponse:
        """Create a new article."""
        # Generate slug if not provided
        slug = request.slug or self._generate_slug(request.title)
        
        # Ensure slug uniqueness
        original_slug = slug
        counter = 1
        while True:
            stmt = select(Article).where(Article.slug == slug)
            result = await self.db.execute(stmt)
            if not result.scalar_one_or_none():
                break
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Convert content to dict
        content_dict = self._content_to_dict(request.content)
        reading_time = self._calculate_reading_time(content_dict)
        
        # Set published_at if status is published
        published_at = None
        if request.status == "published":
            published_at = datetime.now(timezone.utc)
        
        # Create article (avoid touching relationship collections before we set up associations)
        article = Article(
            author_id=uuid.UUID(author_id),
            title=request.title,
            subtitle=request.subtitle,
            slug=slug,
            content=content_dict,
            featured_image=request.featured_image,
            status=request.status,
            reading_time=reading_time,
            published_at=published_at,
        )
        
        self.db.add(article)
        await self.db.flush()
        
        # Handle tags
        if request.tags:
            tags = await self._get_or_create_tags(request.tags)
            # Insert associations explicitly to avoid async lazy-load on relationship
            for tag in tags:
                self.db.add(ArticleTag(article_id=article.id, tag_id=tag.id))
            await self.db.flush()
        # Eagerly load author and tags to avoid lazy loads that cause MissingGreenlet
        await self.db.refresh(article, ["author", "tags"])
        
        # Get author (already loaded)        
        author = article.author
        
        return ArticleDetailResponse(
            id=str(article.id),
            title=article.title,
            subtitle=article.subtitle,
            slug=article.slug,
            content=article.content,
            featured_image=article.featured_image,
            author=self._format_author_response(author),
            reading_time=article.reading_time,
            clap_count=0,
            user_clap_count=0,
            tags=[TagResponse(id=str(t.id), name=t.name, slug=t.slug, description=t.description) for t in article.tags],
            status=article.status,
            published_at=article.published_at,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    async def get_article_by_id(
        self, article_id: str, user_id: Optional[str] = None
    ) -> ArticleDetailResponse:
        """Get article by ID."""
        stmt = select(Article).where(Article.id == uuid.UUID(article_id))
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found",
            )
        
        # Check if user can view (must be published or owner)
        if article.status != "published" and (not user_id or str(article.author_id) != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this article",
            )
        
        await self.db.refresh(article, ["author", "tags"])
        author = article.author
        
        # Get clap counts
        clap_stmt = select(func.sum(Clap.count)).where(Clap.article_id == article.id)
        clap_result = await self.db.execute(clap_stmt)
        total_claps = clap_result.scalar_one() or 0
        
        user_clap_count = 0
        if user_id:
            user_clap_stmt = select(Clap.count).where(
                Clap.article_id == article.id,
                Clap.user_id == uuid.UUID(user_id)
            )
            user_clap_result = await self.db.execute(user_clap_stmt)
            user_clap = user_clap_result.scalar_one_or_none()
            if user_clap:
                user_clap_count = user_clap
        
        return ArticleDetailResponse(
            id=str(article.id),
            title=article.title,
            subtitle=article.subtitle,
            slug=article.slug,
            content=article.content,
            featured_image=article.featured_image,
            author=self._format_author_response(author),
            reading_time=article.reading_time,
            clap_count=total_claps,
            user_clap_count=user_clap_count,
            tags=[TagResponse(id=str(t.id), name=t.name, slug=t.slug, description=t.description) for t in article.tags],
            status=article.status,
            published_at=article.published_at,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    async def get_article_by_slug(
        self, slug: str, user_id: Optional[str] = None
    ) -> ArticleDetailResponse:
        """Get article by slug."""
        stmt = select(Article).where(Article.slug == slug)
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found",
            )
        
        # Check if user can view
        if article.status != "published" and (not user_id or str(article.author_id) != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this article",
            )
        
        await self.db.refresh(article, ["author", "tags"])
        author = article.author
        
        # Get clap counts
        clap_stmt = select(func.sum(Clap.count)).where(Clap.article_id == article.id)
        clap_result = await self.db.execute(clap_stmt)
        total_claps = clap_result.scalar_one() or 0
        
        user_clap_count = 0
        if user_id:
            user_clap_stmt = select(Clap.count).where(
                Clap.article_id == article.id,
                Clap.user_id == uuid.UUID(user_id)
            )
            user_clap_result = await self.db.execute(user_clap_stmt)
            user_clap = user_clap_result.scalar_one_or_none()
            if user_clap:
                user_clap_count = user_clap
        
        return ArticleDetailResponse(
            id=str(article.id),
            title=article.title,
            subtitle=article.subtitle,
            slug=article.slug,
            content=article.content,
            featured_image=article.featured_image,
            author=self._format_author_response(author),
            reading_time=article.reading_time,
            clap_count=total_claps,
            user_clap_count=user_clap_count,
            tags=[TagResponse(id=str(t.id), name=t.name, slug=t.slug, description=t.description) for t in article.tags],
            status=article.status,
            published_at=article.published_at,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    async def update_article(
        self, article_id: str, author_id: str, request: UpdateArticleRequest
    ) -> ArticleDetailResponse:
        """Update an article."""
        stmt = select(Article).where(Article.id == uuid.UUID(article_id))
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found",
            )
        
        # Check ownership
        if str(article.author_id) != author_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this article",
            )
        
        # Update fields
        update_dict = {}
        if request.title is not None:
            update_dict["title"] = request.title
        if request.subtitle is not None:
            update_dict["subtitle"] = request.subtitle
        if request.content is not None:
            content_dict = self._content_to_dict(request.content)
            update_dict["content"] = content_dict
            update_dict["reading_time"] = self._calculate_reading_time(content_dict)
        if request.featured_image is not None:
            update_dict["featured_image"] = request.featured_image
        if request.status is not None:
            update_dict["status"] = request.status
            if request.status == "published" and not article.published_at:
                update_dict["published_at"] = datetime.now(timezone.utc)
        
        # Handle slug update
        if request.slug is not None:
            slug = request.slug
            # Check uniqueness (excluding current article)
            slug_stmt = select(Article).where(
                Article.slug == slug,
                Article.id != article.id
            )
            slug_result = await self.db.execute(slug_stmt)
            if slug_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Slug already exists",
                )
            update_dict["slug"] = slug
        
        # Update article
        if update_dict:
            stmt = (
                update(Article)
                .where(Article.id == article.id)
                .values(**update_dict)
            )
            await self.db.execute(stmt)
        
        # Handle tags update
        if request.tags is not None:
            tags = await self._get_or_create_tags(request.tags)
            # Remove old associations
            await self.db.execute(
                delete(ArticleTag).where(ArticleTag.article_id == article.id)
            )
            # Add new associations explicitly to avoid async lazy-load
            for tag in tags:
                self.db.add(ArticleTag(article_id=article.id, tag_id=tag.id))
            await self.db.flush()
        
        await self.db.commit()
        await self.db.refresh(article, ["author", "tags"])
        
        # Get clap counts
        clap_stmt = select(func.sum(Clap.count)).where(Clap.article_id == article.id)
        clap_result = await self.db.execute(clap_stmt)
        total_claps = clap_result.scalar_one() or 0
        
        user_clap_stmt = select(Clap.count).where(
            Clap.article_id == article.id,
            Clap.user_id == uuid.UUID(author_id)
        )
        user_clap_result = await self.db.execute(user_clap_stmt)
        user_clap = user_clap_result.scalar_one_or_none()
        user_clap_count = user_clap if user_clap else 0
        
        author = article.author
        
        return ArticleDetailResponse(
            id=str(article.id),
            title=article.title,
            subtitle=article.subtitle,
            slug=article.slug,
            content=article.content,
            featured_image=article.featured_image,
            author=self._format_author_response(author),
            reading_time=article.reading_time,
            clap_count=total_claps,
            user_clap_count=user_clap_count,
            tags=[TagResponse(id=str(t.id), name=t.name, slug=t.slug, description=t.description) for t in article.tags],
            status=article.status,
            published_at=article.published_at,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    async def delete_article(self, article_id: str, author_id: str) -> None:
        """Delete an article."""
        stmt = select(Article).where(Article.id == uuid.UUID(article_id))
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found",
            )
        
        # Check ownership
        if str(article.author_id) != author_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this article",
            )
        
        await self.db.delete(article)
        await self.db.commit()

    async def list_articles(
        self,
        user_id: Optional[str] = None,
        author_id: Optional[str] = None,
        tag: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ArticleListItemResponse]:
        """List articles with optional filters."""
        stmt = select(Article).join(User).options(
            selectinload(Article.author),
            selectinload(Article.tags)
        )
        
        # Apply filters
        if status == "published" or (not user_id and not status):
            # Public users can only see published articles
            stmt = stmt.where(Article.status == "published")
        elif status:
            # Authenticated users can filter by status
            stmt = stmt.where(Article.status == status)
            if status != "published" and author_id != user_id:
                # Only show own drafts/archived if not the author
                stmt = stmt.where(Article.author_id == uuid.UUID(user_id))
        
        if author_id:
            stmt = stmt.where(Article.author_id == uuid.UUID(author_id))
        
        if tag:
            stmt = stmt.join(ArticleTag).join(Tag).where(Tag.slug == tag)
        
        # Order by published_at or created_at desc
        stmt = stmt.order_by(
            func.coalesce(Article.published_at, Article.created_at).desc()
        )
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        articles = result.unique().scalars().all()
        
        # Get clap counts for all articles
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

    async def clap_article(
        self, article_id: str, user_id: str, count: int = 1
    ) -> dict:
        """Add claps to an article."""
        # Verify article exists
        stmt = select(Article).where(Article.id == uuid.UUID(article_id))
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found",
            )
        
        # Check if clap already exists
        clap_stmt = select(Clap).where(
            Clap.article_id == uuid.UUID(article_id),
            Clap.user_id == uuid.UUID(user_id)
        )
        clap_result = await self.db.execute(clap_stmt)
        clap = clap_result.scalar_one_or_none()
        
        if clap:
            # Update existing clap
            clap.count = count
        else:
            # Create new clap
            clap = Clap(
                article_id=uuid.UUID(article_id),
                user_id=uuid.UUID(user_id),
                count=count,
            )
            self.db.add(clap)
        
        await self.db.commit()
        await self.db.refresh(clap)
        
        # Get total claps
        total_stmt = select(func.sum(Clap.count)).where(Clap.article_id == uuid.UUID(article_id))
        total_result = await self.db.execute(total_stmt)
        total_claps = total_result.scalar_one() or 0
        
        return {
            "article_id": article_id,
            "user_id": user_id,
            "count": clap.count,
            "total_claps": total_claps,
        }

