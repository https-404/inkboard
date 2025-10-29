from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


#---------------- CONTENT BLOCK SCHEMAS -----------------------------------
class ContentBlockBase(BaseModel):
    """Base schema for content blocks."""
    type: str
    content: Any
    metadata: Optional[Dict[str, Any]] = None


class ParagraphBlock(ContentBlockBase):
    """Paragraph block - plain text content."""
    type: Literal["paragraph"] = "paragraph"
    content: str = Field(..., description="Text content of the paragraph")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional formatting metadata")


class HeadingBlock(ContentBlockBase):
    """Heading block - H1, H2, H3."""
    type: Literal["heading"] = "heading"
    content: str = Field(..., description="Heading text")
    metadata: Dict[str, Any] = Field(..., description="Must include 'level' (1, 2, or 3)")


class ImageBlock(ContentBlockBase):
    """Image block."""
    type: Literal["image"] = "image"
    content: str = Field(..., description="Image URL or path")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional: alt text, caption, alignment"
    )


class CodeBlock(ContentBlockBase):
    """Code block."""
    type: Literal["code"] = "code"
    content: str = Field(..., description="Code content")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional: language, filename"
    )


class QuoteBlock(ContentBlockBase):
    """Quote block."""
    type: Literal["quote"] = "quote"
    content: str = Field(..., description="Quote text")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional: author, source"
    )


class EmbedBlock(ContentBlockBase):
    """Embed block for YouTube, Twitter, etc."""
    type: Literal["embed"] = "embed"
    content: str = Field(..., description="Embed URL")
    metadata: Dict[str, Any] = Field(..., description="Must include 'embedType' (youtube, twitter, etc.)")


class ListBlock(ContentBlockBase):
    """List block (ordered or unordered)."""
    type: Literal["list"] = "list"
    content: List[str] = Field(..., description="List items")
    metadata: Dict[str, Any] = Field(..., description="Must include 'style' ('ordered' or 'unordered')")


# Union type for all block types
ContentBlock = ParagraphBlock | HeadingBlock | ImageBlock | CodeBlock | QuoteBlock | EmbedBlock | ListBlock


#---------------- REQUESTS -----------------------------------
class CreateArticleRequest(BaseModel):
    """Request schema for creating an article."""
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    subtitle: Optional[str] = Field(None, max_length=1000, description="Article subtitle")
    slug: Optional[str] = Field(None, description="URL-friendly slug (auto-generated if not provided)")
    content: List[ContentBlock] = Field(..., description="List of content blocks")
    featured_image: Optional[str] = Field(None, description="Featured image path/URL")
    tags: List[str] = Field(default_factory=list, description="List of tag names")
    status: Literal["draft", "published"] = Field("draft", description="Article status")


class UpdateArticleRequest(BaseModel):
    """Request schema for updating an article."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    subtitle: Optional[str] = Field(None, max_length=1000)
    slug: Optional[str] = Field(None)
    content: Optional[List[ContentBlock]] = None
    featured_image: Optional[str] = Field(None)
    tags: Optional[List[str]] = None
    status: Optional[Literal["draft", "published", "archived"]] = None


class ClapArticleRequest(BaseModel):
    """Request schema for clapping on an article."""
    count: int = Field(1, ge=1, le=50, description="Number of claps (1-50)")


#---------------- RESPONSES -----------------------------------
class TagResponse(BaseModel):
    """Tag response schema."""
    id: str
    name: str
    slug: str
    description: Optional[str] = None


class AuthorResponse(BaseModel):
    """Author information in article response."""
    id: str
    username: str
    fullname: Optional[str] = None
    pfp: Optional[str] = None


class ArticleListItemResponse(BaseModel):
    """Article item in list responses (preview)."""
    id: str
    title: str
    subtitle: Optional[str] = None
    slug: str
    featured_image: Optional[str] = None
    author: AuthorResponse
    reading_time: Optional[int] = None
    clap_count: int = Field(0, description="Total claps on the article")
    tags: List[TagResponse] = Field(default_factory=list)
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ArticleDetailResponse(BaseModel):
    """Full article detail response."""
    id: str
    title: str
    subtitle: Optional[str] = None
    slug: str
    content: List[Dict[str, Any]] = Field(..., description="Content blocks as JSON")
    featured_image: Optional[str] = None
    author: AuthorResponse
    reading_time: Optional[int] = None
    clap_count: int = Field(0, description="Total claps on the article")
    user_clap_count: int = Field(0, description="Current user's claps on the article")
    tags: List[TagResponse] = Field(default_factory=list)
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ClapResponse(BaseModel):
    """Response schema for clap action."""
    article_id: str
    user_id: str
    count: int
    total_claps: int = Field(..., description="Total claps on the article")


