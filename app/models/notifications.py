from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

from app.db import Base


class Notification(Base):
    __tablename__ = "tb_notifications"

    notification_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("tb_users.user_id"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(Text)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])


class Webhook(Base):
    __tablename__ = "tb_webhooks"

    webhook_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("tb_users.user_id"), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(Text, nullable=False)
    secret = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
