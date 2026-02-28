from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

    # 可选：添加自定义验证，例如密码必须包含数字和字母
    @validator('password')
    def password_complexity(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('密码必须包含至少一个数字')
        if not any(char.isalpha() for char in v):
            raise ValueError('密码必须包含至少一个字母')
        return v

class UserResponse(BaseModel):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True