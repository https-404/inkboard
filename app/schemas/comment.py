from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CreateCommentRequest(BaseModel):
    article_id: str = Field(..., description="Article ID the comment belongs to")
    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: Optional[str] = Field(None, description="Parent comment ID for replies")


class UpdateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class CommentReactionRequest(BaseModel):
    value: int = Field(..., description="+1 like, -1 dislike", ge=-1, le=1)


class CommentUser(BaseModel):
    id: str
    username: str
    fullname: Optional[str] = None
    pfp: Optional[str] = None


class CommentResponse(BaseModel):
    id: str
    article_id: str
    user: CommentUser
    content: str
    is_edited: bool
    parent_id: Optional[str] = None
    like_count: int = 0
    dislike_count: int = 0
    reply_count: int = 0
    created_at: datetime
    updated_at: datetime
    # Optional: eager-loaded replies
    replies: Optional[List["CommentResponse"]] = None


class CommentListResponse(BaseModel):
    comments: List[CommentResponse]
    total: int


class CommentReactionResponse(BaseModel):
    comment_id: str
    user_id: str
    value: int
    like_count: int
    dislike_count: int


