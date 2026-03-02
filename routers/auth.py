from fastapi import APIRouter, HTTPException,Depends,status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import get_password_hash,verify_password
from deps.dbdeps import get_db
from schemas import userResponse,userResquest
from models.user import User
from core.atoken import AuthHandler

router = APIRouter()
auth_handler = AuthHandler()  # 单例模式实例全局化对象


@router.post('/register',response_model=userResponse.UserRegisterResponse)
async def register_user(user_in:userResquest.UserCreate,db:AsyncSession = Depends(get_db)):
    """
    用户注册：
    - 检查邮箱和用户名是否已被占用
    - 密码哈希
    - 创建新用户
    - 返回用户信息（不包含密码）
    """
    print("收到的用户数据:", user_in.dict())
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
@router.post('/login',response_model=userResponse.UserLoginResponse)
async def login_user(user_in:userResquest.UserLoginIn,db:AsyncSession = Depends(get_db)):
    """
    用户登录

    """
    result = await db.execute(
        select(User).where(
            User.email == user_in.email)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tokens = auth_handler.encode_login_token(user.id)
    return {
            "user": user,
            "access_token": tokens['access_token'],
            "refresh_token": tokens['refresh_token']
        }
