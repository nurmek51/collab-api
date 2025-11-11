from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from .base import TimestampedModel


class FreelancerStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"


class Freelancer(TimestampedModel):
    freelancer_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    iin: str
    city: str
    email: str
    specializations_with_levels: List[Dict[str, str]] = Field(default_factory=list)
    status: FreelancerStatus = FreelancerStatus.PENDING
    payment_info: Dict[str, str] = Field(default_factory=dict)
    social_links: Dict[str, str] = Field(default_factory=dict)
    portfolio_links: Dict[str, str] = Field(default_factory=dict)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    def to_firestore(self) -> dict:
        data = self.model_dump()
        data["freelancer_id"] = str(self.freelancer_id)
        data["user_id"] = str(self.user_id)
        data["status"] = self.status.value
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        return data

    @classmethod
    def from_firestore(cls, payload: dict) -> "Freelancer":
        created = payload.get("created_at")
        updated = payload.get("updated_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        return cls(
            freelancer_id=uuid.UUID(str(payload["freelancer_id"])),
            user_id=uuid.UUID(str(payload["user_id"])),
            iin=payload.get("iin", ""),
            city=payload.get("city", ""),
            email=payload.get("email", ""),
            specializations_with_levels=list(payload.get("specializations_with_levels", [])),
            status=FreelancerStatus(payload.get("status", FreelancerStatus.PENDING.value)),
            payment_info=payload.get("payment_info") or {},
            social_links=payload.get("social_links") or {},
            portfolio_links=payload.get("portfolio_links") or {},
            avatar_url=payload.get("avatar_url"),
            bio=payload.get("bio"),
            created_at=created or datetime.utcnow(),
            updated_at=updated or datetime.utcnow(),
        )
