"""
创建数据库会话
"""

from sqlalchemy.ext.asyncio import AsyncSession

from models import AsyncSessionFactory


async def get_db():
    """依赖项：获取异步数据库会话"""
    async with AsyncSessionFactory() as session:
        yield session