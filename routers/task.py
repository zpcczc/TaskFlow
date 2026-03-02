
from fastapi import APIRouter, Depends, Query,Header, HTTPException
from oss2.exceptions import status
from sqlalchemy.ext.asyncio import AsyncSession
from deps import dbdeps, userdeps
from schemas.taskRequest import TaskRequest,TaskPriority,TaskStatus,TaskUpdate
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
@router.get('/{task_id}',response_model=TaskResponse)
async def read_task(
        task_id: int,
        db: AsyncSession = Depends(dbdeps.get_db),
        current_user: User = Depends(userdeps.get_current_user),
):
    # 获取任务详情
    task = await TaskService.get_task(db, task_id)
    # 权限控制：只允许创建者和参与者查看
    if task.creator_id != current_user.id and current_user not in task.assignees:
        raise HTTPException(status_code=403,detail='无权查看此任务')
    return task
@router.patch('/{task_id}',response_model=TaskResponse)
async def update_task(
        task_id: int,
        task_in: TaskUpdate,
        db: AsyncSession = Depends(dbdeps.get_db),
        current_user: User = Depends(userdeps.get_current_user),
):
    task = await TaskService.get_task(db, task_id)
    if task.creator_id != current_user.id and current_user not in task.assignees:
        raise HTTPException(status_code=403,detail="无权修改此任务")
    updated_task = await TaskService.update_task(db, task_id, task_in)
    return updated_task
@router.delete('/{task_id}',status_code=204)  # status_code=204 表示删除成功并且不返回任何响应
async def delete_task(
        task_id: int,
        db: AsyncSession = Depends(dbdeps.get_db),
        current_user: User = Depends(userdeps.get_current_user),
):
    task = await TaskService.get_task(db, task_id)
    if task.creator_id != current_user.id:
        raise HTTPException(status_code=403,detail="无权删除此任务")
    await TaskService.delete_task(db, task)
@router.post('/{task_id}/assignees/{user_id}',response_model=TaskResponse)
async def add_assignee(
        task_id: int,
        user_id: int,
        db: AsyncSession = Depends(dbdeps.get_db),
        current_user: User = Depends(userdeps.get_current_user),
):
    # 添加任务执行者，仅创建者可以操作
    task = await TaskService.get_task(db, task_id)
    if task.creator_id != current_user.id:
        raise HTTPException(status_code=403,detail="无权添加其他用户")
    task = await TaskService.add_assignee(db, task, user_id)
    return task
@router.delete('/{task_id}/assignees/{user_id}',response_model=TaskResponse)
async def remove_assignee(
        task_id: int,
        user_id: int,
        db: AsyncSession = Depends(dbdeps.get_db),
        current_user: User = Depends(userdeps.get_current_user),
):
    task = await TaskService.get_task(db, task_id)
    if task.creator_id != current_user.id:
        raise HTTPException(status_code=403,detail="无权移除其他参与者")
    task = await TaskService.remove_assignee(db, task, user_id)
    return task