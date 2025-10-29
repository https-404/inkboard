from typing import Optional
from pydantic import BaseModel, EmailStr


#---------------- REQUESTS -----------------------------------
class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None


#---------------- RESPONSES -----------------------------------
class GetUserProfileResponse(BaseModel):
    userid: str
    fullname: Optional[str] = None
    bio: Optional[str] = None
    pfp: Optional[str] = None
    username: str
    email: EmailStr


