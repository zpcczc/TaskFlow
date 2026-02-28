import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from . import Base

# ---------- 枚举定义 ----------
class TaskStatus(enum.Enum):
    pending = "pending"
    doing = "doing"
    done = "done"

class TaskPriority(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

# ---------- 多对多关联表 ----------
task_assignees = Table(
    "task_assignees",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime, default=datetime.utcnow),
)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(String(1000))
    status = Column(Enum(TaskStatus), default=TaskStatus.pending)
    priority = Column(Enum(TaskPriority), default=TaskPriority.medium)
    due_date = Column(DateTime)
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    creator = relationship(
        "User",
        back_populates="created_tasks",
        foreign_keys=[creator_id])
    assignees = relationship(
        "User",
        secondary=task_assignees,
        back_populates="assigned_tasks")
    notifications = relationship(
        "Notification",
        back_populates="task",
        cascade="all, delete-orphan",
    )