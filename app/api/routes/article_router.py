from fastapi import APIRouter, Depends, Query, Path, status, HTTPException, UploadFile, File
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.deps import get_db
from app.api.deps.auth import get_current_user_id, get_optional_user_id
from app.services.article_service import ArticleService
from app.services.minio_service import get_storage_url
from app.schemas.article import (
    CreateArticleRequest,
    UpdateArticleRequest,
    ArticleDetailResponse,
    ArticleListItemResponse,
    ClapArticleRequest,
    ClapResponse,
    UploadImageResponse,
)

article_router = APIRouter(prefix="/articles", tags=["Articles"])


@article_router.post("", response_model=ArticleDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    request: CreateArticleRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new article.
    
    Requires authentication. Creates an article with block-based content structure.
    """
    article_service = ArticleService(db)
    try:
        return await article_service.create_article(author_id=user_id, request=request)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article slug already exists",
        )


@article_router.get("", response_model=List[ArticleListItemResponse])
async def list_articles(
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    tag: Optional[str] = Query(None, description="Filter by tag slug"),
    status: Optional[str] = Query(None, description="Filter by status (draft/published/archived)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    List articles with optional filters.
    
    Public users can only see published articles.
    Authenticated users can see their own drafts/archived articles.
    """
    article_service = ArticleService(db)
    # Pass None if not authenticated
    current_user_id = user_id if user_id else None
    return await article_service.list_articles(
        user_id=current_user_id,
        author_id=author_id,
        tag=tag,
        status=status,
        limit=limit,
        offset=offset,
    )


@article_router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article_by_id(
    article_id: str = Path(..., description="Article UUID"),
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get article by ID.
    
    Public users can only view published articles.
    Article owners can view their own drafts/archived articles.
    """
    article_service = ArticleService(db)
    current_user_id = user_id if user_id else None
    return await article_service.get_article_by_id(
        article_id=article_id,
        user_id=current_user_id,
    )


@article_router.get("/slug/{slug}", response_model=ArticleDetailResponse)
async def get_article_by_slug(
    slug: str = Path(..., description="Article slug"),
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get article by slug (SEO-friendly URL).
    
    Public users can only view published articles.
    Article owners can view their own drafts/archived articles.
    """
    article_service = ArticleService(db)
    current_user_id = user_id if user_id else None
    return await article_service.get_article_by_slug(
        slug=slug,
        user_id=current_user_id,
    )


@article_router.put("/{article_id}", response_model=ArticleDetailResponse)
async def update_article(
    article_id: str = Path(..., description="Article UUID"),
    request: UpdateArticleRequest = ...,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an article.
    
    Requires authentication. Only the article owner can update.
    """
    article_service = ArticleService(db)
    return await article_service.update_article(
        article_id=article_id,
        author_id=user_id,
        request=request,
    )


@article_router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str = Path(..., description="Article UUID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an article.
    
    Requires authentication. Only the article owner can delete.
    """
    article_service = ArticleService(db)
    await article_service.delete_article(
        article_id=article_id,
        author_id=user_id,
    )


@article_router.post("/{article_id}/clap", response_model=ClapResponse)
async def clap_article(
    article_id: str = Path(..., description="Article UUID"),
    request: ClapArticleRequest = ...,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Clap (like) an article.
    
    Requires authentication. Users can clap 1-50 times per article.
    Updates existing clap if user has already clapped.
    """
    article_service = ArticleService(db)
    result = await article_service.clap_article(
        article_id=article_id,
        user_id=user_id,
        count=request.count,
    )
    return ClapResponse(**result)


@article_router.post("/upload-image", response_model=UploadImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_article_image_endpoint(
    image: UploadFile = File(..., description="Image file to upload"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an image for article content.
    
    Requires authentication. Uploads and compresses the image, returns the storage URL
    that can be used in article ImageBlock content.
    
    The returned image_url should be used in the 'content' field of an ImageBlock.
    """
    from app.services.minio_service import upload_article_image as upload_image_func
    
    image_path = await upload_image_func(image, user_id)
    image_url = get_storage_url(image_path)
    
    return UploadImageResponse(
        image_url=image_url,
        image_path=image_path,
    )

