from datetime import datetime
from typing import List
from schemas.taskRequest import TaskRequest
from schemas.userResponse import UserResponse


class TaskResponse(TaskRequest):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime
    creator: UserResponse
    assignees: List[UserResponse] = []
