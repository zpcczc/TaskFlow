from typing import List

from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from deps import dbdeps,userdeps
from core.atoken import AuthHandler
from deps.dbdeps import get_db
from schemas.userResponse import UserResponse,UsersResponse
from models.user import User
from schemas import userResponse,userResquest
from core.security import get_password_hash,verify_password
router = APIRouter()
auth_handler = AuthHandler()  # 单例模式实例全局化对象

@router.get("/me",response_model=UserResponse)
async def get_user(user_id: int=Depends(auth_handler.auth_access_dependency),db=Depends(get_db)):
    result = await db.execute(
        select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user
@router.put('/me',response_model=UserResponse)
async def update_user(user_in: userResquest.UserUpdate,user_id: int=Depends(auth_handler.auth_access_dependency),db=Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='用户不存在'
        )
    if user_in.username is not None:
        result1 = await db.execute(select(User).where(User.username == user_in.username,user.id != user_id))
        existing_username = result1.scalar_one_or_none()
        if existing_username is None:
            user.username = user_in.username
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用",
            )
    if user_in.password is not None:
        if user_in.old_password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='请输入旧密码'
            )
        if not verify_password(user_in.old_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='原密码错误'
            )
        user.hashed_password = get_password_hash(user_in.password)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
@router.get("/", response_model=List[UsersResponse])
async def read_users(
    db: AsyncSession = Depends(dbdeps.get_db),
    current_user: User = Depends(userdeps.get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取所有用户（分页），返回 id 和 username
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

