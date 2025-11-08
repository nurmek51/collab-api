from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from pydantic import Field

from .base import TimestampedModel


class Client(TimestampedModel):
    client_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    company_ids: List[uuid.UUID] = Field(default_factory=list)

    def to_firestore(self) -> dict:
        data = self.model_dump()
        data["client_id"] = str(self.client_id)
        data["user_id"] = str(self.user_id)
        data["company_ids"] = [str(company_id) for company_id in data.get("company_ids", [])]
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        return data

    @classmethod
    def from_firestore(cls, payload: dict) -> "Client":
        created = payload.get("created_at")
        updated = payload.get("updated_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        return cls(
            client_id=uuid.UUID(str(payload["client_id"])),
            user_id=uuid.UUID(str(payload["user_id"])),
            company_ids=[uuid.UUID(str(cid)) for cid in payload.get("company_ids", [])],
            created_at=created or datetime.utcnow(),
            updated_at=updated or datetime.utcnow(),
        )
