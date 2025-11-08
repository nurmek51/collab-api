from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import TimestampedModel


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class OrderApplication(TimestampedModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    order_id: uuid.UUID
    freelancer_id: uuid.UUID
    company_id: uuid.UUID
    status: ApplicationStatus = ApplicationStatus.PENDING
    specialization_index: Optional[int] = None  # Index of the specialization in order_specializations
    specialization_name: Optional[str] = None  # Name of the specialization for quick reference

    def to_firestore(self) -> dict:
        data = self.model_dump()
        data["id"] = str(self.id)
        data["order_id"] = str(self.order_id)
        data["freelancer_id"] = str(self.freelancer_id)
        data["company_id"] = str(self.company_id)
        data["status"] = self.status.value
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        return data

    @classmethod
    def from_firestore(cls, payload: dict) -> "OrderApplication":
        created = payload.get("created_at")
        updated = payload.get("updated_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        return cls(
            id=uuid.UUID(str(payload["id"])),
            order_id=uuid.UUID(str(payload["order_id"])),
            freelancer_id=uuid.UUID(str(payload["freelancer_id"])),
            company_id=uuid.UUID(str(payload["company_id"])),
            status=ApplicationStatus(payload.get("status", ApplicationStatus.PENDING.value)),
            specialization_index=payload.get("specialization_index"),
            specialization_name=payload.get("specialization_name"),
            created_at=created or datetime.utcnow(),
            updated_at=updated or datetime.utcnow(),
        )
