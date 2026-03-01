from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from core.atoken import AuthHandler
from .dbdeps import get_db
auth_handler = AuthHandler()

async def get_current_user(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录的用户对象
    - 先通过 auth_access_dependency 获取 user_id
    - 再从数据库查询完整用户信息
    - 如果用户不存在或已禁用，抛出 401/403
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账户未激活"
        )
    return user

# 如果需要仅依赖用户 ID（比如user相关接口只需要 ID，避免查询数据库）
def get_current_user_id(
    user_id: int = Depends(auth_handler.auth_access_dependency)
) -> int:
    return user_id