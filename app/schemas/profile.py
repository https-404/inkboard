from typing import Optional
from pydantic import BaseModel, EmailStr

#---------------- REQUESTS -----------------------------------


#---------------- RESPONSES -----------------------------------
class GetUserProfileResponse(BaseModel):
    userid : str
    fullname : Optional[str] = None
    bio: Optional[str] = None
    pfp: Optional[str] = None
    username: str
    email: EmailStr
    

