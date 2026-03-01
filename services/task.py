from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List
from schemas import taskRequest
from models.task import Task
from models.user import User


class TaskService:
    # 这里使用了python中的静态方法，即后续的调用中可以通过类名直接调用而不用在创建一个类的实例
    @staticmethod
    async def create_task(
            db: AsyncSession,
            task_in: taskRequest.TaskCreate,
            creator_id: int,
    ):
        task = Task(**task_in.dict(),creator_id=creator_id)
        db.add(task)
        await db.commit()
        await db.refresh(task)
        result = await db.execute(
            select(Task)
            .where(Task.id == task.id)
            .options(selectinload(Task.creator), selectinload(Task.assignees))
            # selectinload 在查询Task的时候，也查询了关系表，相当于把Task.creator和Task.assignees加载了出来，以防后续加载不出来
        )
        return result.scalar_one()
    @staticmethod
    async def get_task(
            db: AsyncSession,
            task_id: int,
    ):
        result = await db.execute(
            select(Task).where(Task.id == task_id)
            .options(selectinload(Task.creator), selectinload(Task.assignees))
        )
        task = result.scalar_one()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        return task
    @staticmethod
    async def get_tasks(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            status: Optional[taskRequest.TaskStatus] = None,
            priority: Optional[taskRequest.TaskPriority] = None,
            creator_id: Optional[int] = None,
            assignee_id: Optional[int] = None,
    ) ->List[Task]:
        query = select(Task).options(selectinload(Task.creator), selectinload(Task.assignees))
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if creator_id:
            query = query.where(Task.creator_id == creator_id)
        if assignee_id:
            query = query.where(Task.assignees.any(id=assignee_id))
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    @staticmethod
    async def update_task(
            db: AsyncSession,
            task: Task,
            task_in: taskRequest.TaskUpdate
    ):
        """
        这段代码用于部分更新一个数据库对象（task），
        它根据请求数据 task_in 中显式提供的字段，
        动态地更新 task 对象的对应属性，并每更新一个字段就立即提交一次数据库事务。
        1.exclude_unset=True 表示只包含那些在请求中实际设置了值的字段。
        例如，如果请求只提供了 title 和 status，
        那么生成的字典就只有这两个键值对，而不会包含模型定义中其他有默认值的字段。
        这非常适合部分更新（PATCH）场景，因为你只想更新客户端传过来的字段，而不影响其他字段。
        2.setattr(task, field, value)动态地将 task 对象的属性 field 设置为新的值 value。
        这行代码相当于执行类似 task.title = new_title 的操作，但字段名是动态的。
        """
        update_data = task_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
            await db.commit()
            await db.refresh(task)
            result = await db.execute(
                select(Task).where(Task.id == task.id)
                .options(selectinload(Task.creator), selectinload(Task.assignees))
            )
            return result.scalar_one()

    @staticmethod
    async def delete_task(db: AsyncSession, task: Task) -> None:
        await db.delete(task)
        await db.commit()

    @staticmethod
    async def add_assignee(db: AsyncSession, task: Task, user_id: int) -> Task:
        # 检查用户是否存在
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if user not in task.assignees:
            task.assignees.append(user)
            await db.commit()
            await db.refresh(task)
        return task

    @staticmethod
    async def remove_assignee(db: AsyncSession, task: Task, user_id: int) -> Task:
        task.assignees = [u for u in task.assignees if u.id != user_id]
        """
        这段代码是一个列表推导式，它的作用是从 task.assignees 这个列表（包含所有参与该任务的用户）中，
        筛选出所有 ID 不等于 user_id 的用户，然后用这些用户组成一个新的列表，最后将这个新列表重新赋值给 task.assignees。
        """
        await db.commit()
        await db.refresh(task)
        return task
