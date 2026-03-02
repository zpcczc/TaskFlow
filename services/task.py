from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List
from schemas import taskRequest
from models.task import Task
from models.user import User
from models.notification import Notification
from WebSocket.manager import manager

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
        # 创建通知给创建者
        notif = Notification(
            user_id=creator_id,
            task_id=task.id,
            message=f"您创建了任务：{task.title}"
        )
        db.add(notif)
        await db.commit()

        # WebSocket 通知
        await manager.send_personal_message(
            creator_id,
            {
                "type": "task_created",
                "task_id": task.id,
                "title": task.title,
                "message": f"您创建了任务：{task.title}"
            }
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
        # 记录旧状态
        old_status = task.status

        # 只更新提供的字段
        update_data = task_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        # 提交所有更改
        await db.commit()
        # 刷新以获取最新数据
        await db.refresh(task)
        # 重新加载关系（如果后续需要用到 assignees）
        await db.refresh(task, ["assignees"])

        # 检查状态是否变化
        if 'status' in update_data and old_status != task.status:
            # 收集需要通知的用户：创建者 + 所有执行者
            user_ids = {task.creator_id}
            user_ids.update(a.id for a in task.assignees)

            # 1. 存入数据库通知
            notifications = []
            for uid in user_ids:
                notif = Notification(
                    user_id=uid,
                    task_id=task.id,
                    message=f"任务 '{task.title}' 状态从 {old_status.value} 变为 {task.status.value}"
                )
                notifications.append(notif)
            db.add_all(notifications)
            await db.commit()  # 提交通知

            # 2. 发送 WebSocket 实时消息
            for uid in user_ids:
                await manager.send_personal_message(
                    uid,
                    {
                        "type": "task_status_changed",
                        "task_id": task.id,
                        "old_status": old_status.value,
                        "new_status": task.status.value,
                        "message": f"任务 '{task.title}' 状态已变更"
                    }
                )

        # 最终返回完整的任务对象（包含关系）
        result = await db.execute(
            select(Task)
            .where(Task.id == task.id)
            .options(selectinload(Task.creator), selectinload(Task.assignees))
        )
        return result.scalar_one()

    @staticmethod
    async def delete_task(db: AsyncSession, task: Task) -> None:
        # 预先加载 assignees
        await db.refresh(task, ["assignees"])
        user_ids = {task.creator_id}
        user_ids.update(a.id for a in task.assignees)
        # 发送通知（可以先发 WebSocket，再删任务）
        for uid in user_ids:
            await manager.send_personal_message(
                uid,
                {
                    "type": "task_deleted",
                    "task_id": task.id,
                    "title": task.title,
                    "message": f"任务 '{task.title}' 已被删除"
                }
            )
        # Notification 中 task_id 设置了 ondelete="CASCADE"，删除任务时会自动删除关联的通知。
        await db.delete(task)
        await db.commit()

    @staticmethod
    async def add_assignee(db: AsyncSession, task: Task, user_id: int):
        # 检查用户是否存在
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if user not in task.assignees:
            task.assignees.append(user)
            await db.commit()
            await db.refresh(task)

            # 创建通知给被分配者
            notif = Notification(
                user_id=user_id,
                task_id=task.id,
                message=f"您被分配了任务：{task.title}"
            )
            db.add(notif)
            await db.commit()

            # WebSocket 通知
            await manager.send_personal_message(
                user_id,
                {
                    "type": "task_assigned",
                    "task_id": task.id,
                    "title": task.title,
                    "message": f"您被分配了任务：{task.title}"
                }
            )
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
