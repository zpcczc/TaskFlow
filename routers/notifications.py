from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from deps import dbdeps,userdeps
from fastapi import APIRouter, Depends, HTTPException, status

from models.notification import Notification
from models.user import User
from schemas.notiRequest import NotificationBase,NotificationCreate
from schemas.notiResponse import NotificationResponse


router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    db: AsyncSession = Depends(dbdeps.get_db),
    current_user: User = Depends(userdeps.get_current_user),
    skip: int = 0,
    limit: int = 50,
):
    """
    获取当前用户的通知列表（按时间倒序）
    """
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(dbdeps.get_db),
    current_user: User = Depends(userdeps.get_current_user),
):
    """
    删除指定的通知（只能删除自己的）
    """
    notification = await db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="通知不存在")
    await db.delete(notification)
    await db.commit()