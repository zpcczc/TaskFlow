from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
class UserResponse(BaseModel):
    id:int
    email: EmailStr
    username: str
    is_active: bool



class UserRegisterResponse(UserResponse):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLoginResponse(BaseModel):
    user:UserResponse
    access_token: str
    refresh_token: str

class UsersResponse(BaseModel):
    id: int
    username: str
