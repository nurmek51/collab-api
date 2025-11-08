from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict, Field

from .base import TimestampedModel


class Role(str, enum.Enum):
    CLIENT = "client"
    FREELANCER = "freelancer"
    ADMIN = "admin"


class User(TimestampedModel):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: Optional[str] = None
    surname: Optional[str] = None
    phone_number: Optional[str] = None
    roles: List[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)

    def to_firestore(self) -> dict:
        data = self.model_dump()
        data["user_id"] = str(self.user_id)
        data["roles"] = list(dict.fromkeys(data.get("roles", [])))
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        if isinstance(data.get("updated_at"), datetime):
            data["updated_at"] = data["updated_at"].isoformat()
        return data

    @classmethod
    def from_firestore(cls, payload: Optional[dict]) -> Optional["User"]:
        if not payload:
            return None
        created = payload.get("created_at")
        updated = payload.get("updated_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        return cls(
            user_id=uuid.UUID(str(payload["user_id"])),
            name=payload.get("name"),
            surname=payload.get("surname"),
            phone_number=payload.get("phone_number"),
            roles=list(payload.get("roles", [])),
            created_at=created or datetime.utcnow(),
            updated_at=updated or datetime.utcnow(),
        )
