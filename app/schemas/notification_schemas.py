from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    user_id: int
    type: str
    title: str
    message: str
    data: Optional[dict] = None


class NotificationResponse(BaseModel):
    notification_id: int
    user_id: int
    type: str
    title: str
    message: str
    data: Optional[dict]
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int
    total: int


class WebhookRegisterRequest(BaseModel):
    url: HttpUrl
    events: List[str] = Field(..., min_items=1)
    secret: Optional[str] = None


class WebhookResponse(BaseModel):
    webhook_id: int
    user_id: int
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WebSocketMessage(BaseModel):
    type: str
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
