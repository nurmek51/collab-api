import uuid
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    HELP_REQUEST = "help_request"
    ORDER_UPDATE = "order_update"
    USER_ACTION = "user_action"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    READ = "read"
    RESOLVED = "resolved"


class NotificationResponse(BaseModel):
    notification_id: uuid.UUID
    type: NotificationType
    status: NotificationStatus
    title: str
    message: str
    user_id: uuid.UUID
    client_id: Optional[uuid.UUID] = None
    order_id: Optional[uuid.UUID] = None
    reason: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NotificationUpdate(BaseModel):
    status: Optional[NotificationStatus] = None
    admin_notes: Optional[str] = Field(None, max_length=1000)