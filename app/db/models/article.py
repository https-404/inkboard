import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Index, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class Article(Base):
    """
    Represents an article/post on the platform.
    Uses block-based content structure similar to Medium.
    """
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Author relationship
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    # Basic metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    subtitle: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    slug: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)
    
    # Content structure - block-based (stored as JSONB for flexibility)
    # Each block has: {type, content, metadata}
    # Types: paragraph, heading, image, code, quote, embed, list
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Featured image
    featured_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Status: draft, published, archived
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        server_default="draft",
        index=True
    )
    
    # Publishing
    published_at: Mapped["DateTime | None"] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        index=True
    )
    
    # Reading time (in minutes, calculated)
    reading_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Relationships
    author = relationship("User", back_populates="articles")
    tags = relationship("Tag", secondary="article_tag", back_populates="articles")
    claps = relationship("Clap", back_populates="article", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_article_status"
        ),
    )


class Tag(Base):
    """
    Represents a tag/category for articles.
    """
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    articles = relationship("Article", secondary="article_tag", back_populates="tags")


# Association table for many-to-many relationship
class ArticleTag(Base):
    """
    Association table for article-tag many-to-many relationship.
    """
    __tablename__ = "article_tag"
    
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("article.id", ondelete="CASCADE"), 
        primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tag.id", ondelete="CASCADE"), 
        primary_key=True
    )
    
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )


class Clap(Base):
    """
    Represents a clap (like) on an article.
    """
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("article.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Relationships
    article = relationship("Article", back_populates="claps")
    user = relationship("User")
    
    # Unique constraint: one clap record per user per article
    __table_args__ = (
        Index("uq_article_user_clap", article_id, user_id, unique=True),
    )


