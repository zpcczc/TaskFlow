from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from . import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)  # 增加长度，适应更长的哈希
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    created_tasks = relationship(
        "Task",
        back_populates="creator",
        foreign_keys="[Task.creator_id]",
        cascade="all, delete-orphan",
    )
    assigned_tasks = relationship(
        "Task",
        secondary="task_assignees",  # 使用字符串表名引用关联表
        back_populates="assignees",
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # 如果需要额外索引，可以在这里添加
    __table_args__ = (
        Index("ix_users_created_at", created_at),
        # 其他联合索引等
    )