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

class UserLoginIn(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """更新用户信息（所有字段可选）"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    old_password: Optional[str] = Field(None, min_length=6, max_length=100)  # 修改密码时必须提供

    @validator('password')
    def validate_password(cls, v, values):
        if v is not None:
            # 密码复杂度校验（示例：必须包含字母和数字）
            if not any(char.isdigit() for char in v):
                raise ValueError('密码必须包含至少一个数字')
            if not any(char.isalpha() for char in v):
                raise ValueError('密码必须包含至少一个字母')
            # 如果提供了新密码，必须同时提供旧密码
            if 'old_password' not in values or values['old_password'] is None:
                raise ValueError('修改密码时必须提供旧密码')
        return v

    @validator('old_password')
    def validate_old_password(cls, v, values):
        # 如果提供了旧密码但没提供新密码，也允许（但通常不会单独使用）
        return v