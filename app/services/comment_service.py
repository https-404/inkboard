import uuid
from typing import List, Optional
from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.db.models.comment import Comment, CommentReaction
from app.db.models.user import User
from app.db.models.article import Article
from app.schemas.comment import (
    CreateCommentRequest,
    UpdateCommentRequest,
    CommentResponse,
    CommentUser,
    CommentListResponse,
    CommentReactionRequest,
    CommentReactionResponse,
)
from app.services.minio_service import get_storage_url


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _format_user(self, user: User) -> CommentUser:
        fullname = None
        if user.first_name or user.last_name:
            fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
        pfp_url = get_storage_url(user.pfp) if user.pfp else None
        return CommentUser(id=str(user.id), username=user.username, fullname=fullname, pfp=pfp_url)

    async def _counts_for_comment(self, comment_id: uuid.UUID) -> tuple[int, int, int]:
        like_stmt = select(func.count()).where(CommentReaction.comment_id == comment_id, CommentReaction.value == 1)
        dislike_stmt = select(func.count()).where(CommentReaction.comment_id == comment_id, CommentReaction.value == -1)
        reply_stmt = select(func.count()).where(Comment.parent_id == comment_id)
        like_count = (await self.db.execute(like_stmt)).scalar_one()
        dislike_count = (await self.db.execute(dislike_stmt)).scalar_one()
        reply_count = (await self.db.execute(reply_stmt)).scalar_one()
        return int(like_count), int(dislike_count), int(reply_count)

    async def create_comment(self, user_id: str, req: CreateCommentRequest) -> CommentResponse:
        # Validate article exists
        art_stmt = select(Article.id).where(Article.id == uuid.UUID(req.article_id))
        if not (await self.db.execute(art_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

        parent_id = uuid.UUID(req.parent_id) if req.parent_id else None
        if parent_id:
            # ensure parent exists and belongs to same article
            p_stmt = select(Comment).where(Comment.id == parent_id)
            parent = (await self.db.execute(p_stmt)).scalar_one_or_none()
            if not parent or str(parent.article_id) != req.article_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parent comment")

        comment = Comment(
            article_id=uuid.UUID(req.article_id),
            user_id=uuid.UUID(user_id),
            parent_id=parent_id,
            content=req.content,
        )
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment, ["user"])

        like_count, dislike_count, reply_count = await self._counts_for_comment(comment.id)
        return CommentResponse(
            id=str(comment.id),
            article_id=str(comment.article_id),
            user=self._format_user(comment.user),
            content=comment.content,
            is_edited=comment.is_edited,
            parent_id=str(comment.parent_id) if comment.parent_id else None,
            like_count=like_count,
            dislike_count=dislike_count,
            reply_count=reply_count,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    async def list_comments(self, article_id: str, limit: int = 50, offset: int = 0) -> CommentListResponse:
        # top-level comments only (parent_id is null)
        stmt = (
            select(Comment)
            .options(selectinload(Comment.user))
            .where(Comment.article_id == uuid.UUID(article_id), Comment.parent_id.is_(None))
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        comments = result.scalars().all()

        items: List[CommentResponse] = []
        for c in comments:
            like_count, dislike_count, reply_count = await self._counts_for_comment(c.id)
            items.append(
                CommentResponse(
                    id=str(c.id),
                    article_id=str(c.article_id),
                    user=self._format_user(c.user),
                    content=c.content,
                    is_edited=c.is_edited,
                    parent_id=None,
                    like_count=like_count,
                    dislike_count=dislike_count,
                    reply_count=reply_count,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )

        # total could be added with a count query; quick approximation
        return CommentListResponse(comments=items, total=len(items))

    async def list_replies(self, comment_id: str, limit: int = 50, offset: int = 0) -> CommentListResponse:
        stmt = (
            select(Comment)
            .options(selectinload(Comment.user))
            .where(Comment.parent_id == uuid.UUID(comment_id))
            .order_by(Comment.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        comments = result.scalars().all()

        items: List[CommentResponse] = []
        for c in comments:
            like_count, dislike_count, reply_count = await self._counts_for_comment(c.id)
            items.append(
                CommentResponse(
                    id=str(c.id),
                    article_id=str(c.article_id),
                    user=self._format_user(c.user),
                    content=c.content,
                    is_edited=c.is_edited,
                    parent_id=str(c.parent_id) if c.parent_id else None,
                    like_count=like_count,
                    dislike_count=dislike_count,
                    reply_count=reply_count,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )

        return CommentListResponse(comments=items, total=len(items))

    async def update_comment(self, user_id: str, comment_id: str, req: UpdateCommentRequest) -> CommentResponse:
        stmt = select(Comment).options(selectinload(Comment.user)).where(Comment.id == uuid.UUID(comment_id))
        result = await self.db.execute(stmt)
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if str(comment.user_id) != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

        comment.content = req.content
        comment.is_edited = True
        await self.db.flush()
        await self.db.refresh(comment, ["user"])
        like_count, dislike_count, reply_count = await self._counts_for_comment(comment.id)
        return CommentResponse(
            id=str(comment.id),
            article_id=str(comment.article_id),
            user=self._format_user(comment.user),
            content=comment.content,
            is_edited=comment.is_edited,
            parent_id=str(comment.parent_id) if comment.parent_id else None,
            like_count=like_count,
            dislike_count=dislike_count,
            reply_count=reply_count,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    async def delete_comment(self, user_id: str, comment_id: str) -> None:
        stmt = select(Comment).where(Comment.id == uuid.UUID(comment_id))
        result = await self.db.execute(stmt)
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if str(comment.user_id) != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        await self.db.delete(comment)
        await self.db.flush()

    async def react(self, user_id: str, comment_id: str, req: CommentReactionRequest) -> CommentReactionResponse:
        # toggle semantics: if same value exists, remove; if different or none, set
        stmt = select(CommentReaction).where(
            CommentReaction.comment_id == uuid.UUID(comment_id),
            CommentReaction.user_id == uuid.UUID(user_id),
        )
        result = await self.db.execute(stmt)
        reaction = result.scalar_one_or_none()

        if req.value not in (-1, 0, 1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reaction value")

        if reaction:
            if req.value == 0 or reaction.value == req.value:
                await self.db.delete(reaction)
            else:
                reaction.value = req.value
        else:
            if req.value != 0:
                reaction = CommentReaction(
                    comment_id=uuid.UUID(comment_id),
                    user_id=uuid.UUID(user_id),
                    value=req.value,
                )
                self.db.add(reaction)

        await self.db.flush()

        # counts
        like_count, dislike_count, _ = await self._counts_for_comment(uuid.UUID(comment_id))
        return CommentReactionResponse(
            comment_id=comment_id,
            user_id=user_id,
            value=req.value,
            like_count=like_count,
            dislike_count=dislike_count,
        )


