from datetime import datetime
from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 唯一主键
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)  # 某些通知可能不关联具体任务，设为可空
    message = Column(String(255), nullable=False)  # 长度可根据需要调整
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    user = relationship("User", back_populates="notifications")  # 建议使用 back_populates 明确双向关系
    task = relationship("Task", back_populates="notifications")

    # 索引和约束
    __table_args__ = (
        Index("ix_notifications_user_id", user_id),
        Index("ix_notifications_is_read", is_read),
        # 可选：确保同一用户对同一任务只有一条通知（如果业务需要）
        # UniqueConstraint('user_id', 'task_id', name='uq_user_task_notification'),
    )