from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from deps import dbdeps, userdeps
from schemas.taskRequest import TaskRequest,TaskPriority,TaskStatus
from schemas.taskResponse import TaskResponse
from models.user import User
from services.task import TaskService
from typing import List,Optional

router = APIRouter(prefix="/task", tags=["任务"])


@router.post('/',response_model=TaskResponse)
async def create_task(
        task_in: TaskRequest,
        db: AsyncSession = Depends(dbdeps.get_db),
        current_user: User = Depends(userdeps.get_current_user),
):
    task = await TaskService.create_task(db,task_in,current_user.id)
    return task
@router.get("/", response_model=List[TaskResponse])
async def read_tasks(
    db: AsyncSession = Depends(dbdeps.get_db),
    current_user: User = Depends(userdeps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    creator_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
):
    """获取任务列表（支持过滤）"""
    # 权限控制：普通用户只能看到自己创建或参与的任务可根据需求调整
    # 这里简单实现管理员可见所有，普通用户限制（需要添加角色判断）
    # 为简化，我们先实现所有用户可见所有任务（公开），后续再完善
    tasks = await TaskService.get_tasks(
        db, skip, limit, status, priority, creator_id, assignee_id
    )
    return tasks