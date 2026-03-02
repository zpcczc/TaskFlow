from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationBase(BaseModel):
    message: str
    is_read: bool = False
    task_id: Optional[int] = None

class NotificationCreate(NotificationBase):
    user_id: int