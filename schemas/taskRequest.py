from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    doing = "doing"
    done = "done"

class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class TaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None,max_length=100)
    status: TaskStatus = TaskStatus.pending   # 默认为等待
    priority: TaskPriority = TaskPriority.medium
    due_date: Optional[datetime] = None

class TaskCreate(TaskRequest):
    """
    除了基础字段不需要别的字段，因为创建者可以从token获取
    """
    pass
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None