from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notifications import Notification, Webhook
from app.schemas.notification_schemas import NotificationCreate
from app.services.websocket_service import manager
from datetime import datetime
import httpx
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self, notification_data: NotificationCreate
    ) -> Notification:
        notification = Notification(
            user_id=notification_data.user_id,
            type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            data=notification_data.data,
            read=False,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        await self._send_websocket_notification(notification)
        await self._trigger_webhooks(notification)

        return notification

    async def _send_websocket_notification(self, notification: Notification):
        try:
            message = {
                "type": "notification",
                "data": {
                    "id": str(notification.id),
                    "type": notification.type,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data,
                    "created_at": notification.created_at.isoformat(),
                },
            }
            await manager.send_personal_message(message, str(notification.user_id))
        except Exception as e:
            logger.error(f"WebSocket notification error: {e}")

    async def _trigger_webhooks(self, notification: Notification):
        try:
            result = await self.db.execute(
                select(Webhook).where(
                    Webhook.user_id == notification.user_id,
                    Webhook.active == True,
                    Webhook.events.contains([notification.type]),
                )
            )
            webhooks = result.scalars().all()

            for webhook in webhooks:
                await self._send_webhook(webhook, notification)
        except Exception as e:
            logger.error(f"Webhook trigger error: {e}")

    async def _send_webhook(self, webhook: Webhook, notification: Notification):
        try:
            payload = {
                "event": notification.type,
                "notification_id": str(notification.id),
                "user_id": str(notification.user_id),
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "timestamp": notification.created_at.isoformat(),
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    webhook.last_triggered = datetime.utcnow()
                    await self.db.commit()
                else:
                    logger.warning(
                        f"Webhook failed: {webhook.url} - Status: {response.status_code}"
                    )
        except Exception as e:
            logger.error(f"Webhook send error to {webhook.url}: {e}")

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id, Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.read = True
            notification.read_at = datetime.utcnow()
            await self.db.commit()
            return True
        return False

    async def get_user_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50
    ):
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.read == False)

        query = query.order_by(Notification.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()
