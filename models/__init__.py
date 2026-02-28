
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
DATABASE_URL="mysql+aiomysql://root:123456@127.0.0.1:3306/TaskFlow?charset=utf8"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 开启SQL日志便于调试
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_recycle=3600,  # 连接回收时间（秒）
    pool_size=10,  # 连接池大小
    max_overflow=20  # 最大溢出连接数
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
Base = declarative_base()


from . import notification
from . import user
from . import task