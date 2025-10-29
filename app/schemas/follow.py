from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


#---------------- REQUESTS -----------------------------------
class FollowUserRequest(BaseModel):
    """Request to follow a user (no body needed, just user ID in path)."""
    pass


#---------------- RESPONSES -----------------------------------
class UserBasicInfo(BaseModel):
    """Basic user information for follow lists."""
    id: str
    username: str
    fullname: Optional[str] = None
    pfp: Optional[str] = None
    bio: Optional[str] = None


class FollowResponse(BaseModel):
    """Response for follow/unfollow actions."""
    follower_id: str
    following_id: str
    message: str
    following: bool = Field(..., description="Whether the follow relationship exists")


class FollowersListResponse(BaseModel):
    """Response for list of followers."""
    user_id: str
    followers: List[UserBasicInfo] = Field(default_factory=list)
    total: int = Field(..., description="Total number of followers")


class FollowingListResponse(BaseModel):
    """Response for list of users being followed."""
    user_id: str
    following: List[UserBasicInfo] = Field(default_factory=list)
    total: int = Field(..., description="Total number of users being followed")


class FollowStatusResponse(BaseModel):
    """Response for checking follow status."""
    is_following: bool = Field(..., description="Whether current user follows target user")
    follower_id: str
    following_id: str

