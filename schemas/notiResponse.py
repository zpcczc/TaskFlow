from pydantic import BaseModel
from datetime import datetime
from schemas.notiRequest import  NotificationBase
class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    created_at: datetime