from fastapi import APIRouter, HTTPException,Depends,status


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_password_hash
from deps.dbdeps import get_db
import schemas.user
from models.user import User


router = APIRouter(prefix="/auth", tags=["认证"])



@router.post('/register',response_model=schemas.user.UserResponse)
async def register_user(user_in:schemas.user.UserCreate,db:AsyncSession = Depends(get_db)):
    """
    用户注册：
    - 检查邮箱和用户名是否已被占用
    - 密码哈希
    - 创建新用户
    - 返回用户信息（不包含密码）
    """
    # 检查邮箱是否存在
    existing_email = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )
    # 检查用户是否存在
    existing_username = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已被注使用",
        )
    # 创建新用户对象
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user