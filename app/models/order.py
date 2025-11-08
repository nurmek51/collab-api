from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import TimestampedModel


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"


class OrderCompleteStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROCESS = "in_process"
    COMPLETED = "completed"


class Order(TimestampedModel):
    order_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    order_description: str
    company_id: uuid.UUID
    order_status: OrderStatus = OrderStatus.PENDING
    order_complete_status: OrderCompleteStatus = OrderCompleteStatus.PENDING
    order_title: Optional[str] = None
    chat_link: Optional[str] = None
    requirements: Optional[str] = None
    order_condition: Optional[Dict[str, Any]] = None
    contracts: Optional[Dict[str, Any]] = None
    order_specializations: Optional[List[Dict[str, Any]]] = None

    def to_firestore(self) -> dict:
        data = self.model_dump()
        data["order_id"] = str(self.order_id)
        data["company_id"] = str(self.company_id)
        data["order_status"] = self.order_status.value
        data["order_complete_status"] = self.order_complete_status.value
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        return data

    @classmethod
    def from_firestore(cls, payload: dict) -> "Order":
        created = payload.get("created_at")
        updated = payload.get("updated_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        return cls(
            order_id=uuid.UUID(str(payload["order_id"])),
            order_description=payload.get("order_description", ""),
            company_id=uuid.UUID(str(payload["company_id"])),
            order_status=OrderStatus(payload.get("order_status", OrderStatus.PENDING.value)),
            order_complete_status=OrderCompleteStatus(payload.get("order_complete_status", OrderCompleteStatus.PENDING.value)),
            order_title=payload.get("order_title"),
            chat_link=payload.get("chat_link"),
            requirements=payload.get("requirements"),
            order_condition=payload.get("order_condition"),
            contracts=payload.get("contracts"),
            order_specializations=payload.get("order_specializations"),
            created_at=created or datetime.utcnow(),
            updated_at=updated or datetime.utcnow(),
        )
