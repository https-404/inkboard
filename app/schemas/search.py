from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


#---------------- REQUESTS -----------------------------------
class SearchUsersRequest(BaseModel):
    q: str = Field(..., min_length=1, description="Search query for username")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")


#---------------- RESPONSES -----------------------------------
class SearchUserItem(BaseModel):
    """Individual user item in search results."""
    userid: str
    fullname: Optional[str] = None
    bio: Optional[str] = None
    pfp: Optional[str] = None
    username: str
    email: EmailStr


class SearchUsersResponse(BaseModel):
    """Response for user search."""
    results: List[SearchUserItem]
    total: int = Field(..., description="Total number of results found")
    query: str = Field(..., description="The search query used")
    limit: int = Field(..., description="Maximum results limit applied")

