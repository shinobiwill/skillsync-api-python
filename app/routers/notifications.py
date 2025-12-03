from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db import get_db
from app.core.dependencies import get_current_user
from app.models.models import User
from app.schemas.notification_schemas import (
    NotificationResponse,
    WebhookRegisterRequest,
    WebhookResponse,
)
from app.services.notification_service import NotificationService
from app.models.notifications import Webhook
from sqlalchemy import select
import uuid

router = APIRouter(prefix="/api/trpc", tags=["notifications"])


@router.get("/notifications.list")
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[NotificationResponse]:
    service = NotificationService(db)
    user_id = current_user.get("sub", current_user.get("id"))
    notifications = await service.get_user_notifications(
        str(user_id), unread_only, limit
    )

    return [
        NotificationResponse(
            id=str(n.id),
            user_id=str(n.user_id),
            type=n.type,
            title=n.title,
            message=n.message,
            data=n.data,
            read=n.read,
            created_at=n.created_at,
            read_at=n.read_at,
        )
        for n in notifications
    ]


@router.post("/notifications.markAsRead")
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    user_id = current_user.get("sub", current_user.get("id"))
    success = await service.mark_as_read(notification_id, str(user_id))

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"success": True, "message": "Notification marked as read"}


@router.post("/webhooks.register")
async def register_webhook(
    request: WebhookRegisterRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    user_id = current_user.get("sub", current_user.get("id"))
    webhook = Webhook(
        id=uuid.uuid4(),
        user_id=user_id,
        url=request.url,
        events=request.events,
        active=True,
    )

    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    return WebhookResponse(
        id=str(webhook.id),
        user_id=str(webhook.user_id),
        url=webhook.url,
        events=webhook.events,
        active=webhook.active,
        created_at=webhook.created_at,
    )


@router.get("/webhooks.list")
async def list_webhooks(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> List[WebhookResponse]:
    user_id = current_user.get("sub", current_user.get("id"))
    result = await db.execute(select(Webhook).where(Webhook.user_id == user_id))
    webhooks = result.scalars().all()

    return [
        WebhookResponse(
            id=str(w.id),
            user_id=str(w.user_id),
            url=w.url,
            events=w.events,
            active=w.active,
            created_at=w.created_at,
            last_triggered=w.last_triggered,
        )
        for w in webhooks
    ]


@router.delete("/webhooks.delete")
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.get("sub", current_user.get("id"))
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == user_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    await db.commit()

    return {"success": True, "message": "Webhook deleted"}
