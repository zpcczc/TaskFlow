from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from deps import dbdeps,userdeps
from fastapi import APIRouter, Depends, HTTPException
from models.notification import Notification
from models.user import User
from schemas.notiResponse import NotificationResponse
from sqlalchemy import select, func

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    db: AsyncSession = Depends(dbdeps.get_db),
    current_user: User = Depends(userdeps.get_current_user),
    skip: int = 0,
    limit: int = 20,
):
    """获取当前用户的通知列表（分页，按时间倒序）"""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    notifications = result.scalars().all()
    return notifications

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

@router.get("/unread-count", response_model=int)
async def get_unread_count(
    db: AsyncSession = Depends(dbdeps.get_db),
    current_user: User = Depends(userdeps.get_current_user),
):
    """获取当前用户的未读通知数量"""
    result = await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    )
    return result.scalar()
