from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.deps import get_db
from app.api.deps.auth import get_current_user_id
from app.services.comment_service import CommentService
from app.schemas.comment import (
    CreateCommentRequest,
    UpdateCommentRequest,
    CommentListResponse,
    CommentResponse,
    CommentReactionRequest,
    CommentReactionResponse,
)


comment_router = APIRouter(prefix="/comments", tags=["Comments"])


@comment_router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    req: CreateCommentRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    return await service.create_comment(user_id, req)


@comment_router.get("/article/{article_id}", response_model=CommentListResponse)
async def list_article_comments(
    article_id: str = Path(..., description="Article ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    return await service.list_comments(article_id, limit, offset)


@comment_router.get("/{comment_id}/replies", response_model=CommentListResponse)
async def list_replies(
    comment_id: str = Path(..., description="Parent comment ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    return await service.list_replies(comment_id, limit, offset)


@comment_router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str = Path(...),
    req: UpdateCommentRequest = ...,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    return await service.update_comment(user_id, comment_id, req)


@comment_router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str = Path(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    await service.delete_comment(user_id, comment_id)
    return None


@comment_router.post("/{comment_id}/react", response_model=CommentReactionResponse)
async def react_comment(
    comment_id: str = Path(...),
    req: CommentReactionRequest = ...,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    return await service.react(user_id, comment_id, req)


