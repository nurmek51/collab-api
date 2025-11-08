from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import TimestampedModel


class NotificationType(str, enum.Enum):
    HELP_REQUEST = "help_request"
    ORDER_UPDATE = "order_update"
    USER_ACTION = "user_action"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    READ = "read"
    RESOLVED = "resolved"


class Notification(TimestampedModel):
    notification_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: NotificationType
    status: NotificationStatus = NotificationStatus.PENDING
    title: str
    message: str
    user_id: uuid.UUID  # User who triggered the notification
    client_id: Optional[uuid.UUID] = None
    order_id: Optional[uuid.UUID] = None
    reason: Optional[str] = None
    admin_notes: Optional[str] = None

    def to_firestore(self) -> dict:
        data = self.model_dump()
        data["notification_id"] = str(self.notification_id)
        data["user_id"] = str(self.user_id)
        data["type"] = self.type.value
        data["status"] = self.status.value
        if self.client_id:
            data["client_id"] = str(self.client_id)
        if self.order_id:
            data["order_id"] = str(self.order_id)
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        return data

    @classmethod
    def from_firestore(cls, payload: dict) -> "Notification":
        created = payload.get("created_at")
        updated = payload.get("updated_at")

        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)

        return cls(
            notification_id=uuid.UUID(payload["notification_id"]),
            type=NotificationType(payload["type"]),
            status=NotificationStatus(payload["status"]),
            title=payload["title"],
            message=payload["message"],
            user_id=uuid.UUID(payload["user_id"]),
            client_id=uuid.UUID(payload["client_id"]) if payload.get("client_id") else None,
            order_id=uuid.UUID(payload["order_id"]) if payload.get("order_id") else None,
            reason=payload.get("reason"),
            admin_notes=payload.get("admin_notes"),
            created_at=created,
            updated_at=updated,
        )