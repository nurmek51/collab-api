from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import Field

from .base import TimestampedModel


class Company(TimestampedModel):
    company_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    client_id: uuid.UUID
    owner_ids: List[uuid.UUID] = Field(default_factory=list)
    company_industry: Optional[str] = None
    client_position: Optional[str] = None
    company_name: Optional[str] = None
    company_size: Optional[int] = None
    company_logo: Optional[str] = None
    company_description: Optional[str] = None
    company_orders: List[uuid.UUID] = Field(default_factory=list)
    normalized_company_name: Optional[str] = None

    def to_firestore(self) -> dict:
        data = self.model_dump()
        data["company_id"] = str(self.company_id)
        data["client_id"] = str(self.client_id)
        data["owner_ids"] = [str(owner_id) for owner_id in self.owner_ids]
        data["company_orders"] = [str(order_id) for order_id in self.company_orders]
        if self.company_name:
            data["normalized_company_name"] = (self.company_name or "").strip().lower()
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        return data

    @classmethod
    def from_firestore(cls, payload: dict) -> "Company":
        created = payload.get("created_at")
        updated = payload.get("updated_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        
        try:
            client_uuid = uuid.UUID(str(payload["client_id"]))
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid client_id in payload: {payload.get('client_id', 'MISSING')} - {e}")
        
        try:
            owner_ids_raw = payload.get("owner_ids", [])
            owner_ids = []
            for oid in owner_ids_raw:
                if oid and str(oid).strip():  # Only process non-empty values
                    owner_ids.append(uuid.UUID(str(oid)))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid owner_ids in payload: {payload.get('owner_ids', 'MISSING')} - {e}")
            
        if client_uuid not in owner_ids:
            owner_ids.append(client_uuid)

        try:
            company_id = uuid.UUID(str(payload["company_id"]))
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid company_id in payload: {payload.get('company_id', 'MISSING')} - {e}")

        try:
            company_orders_raw = payload.get("company_orders", [])
            company_orders = []
            for oid in company_orders_raw:
                if oid and str(oid).strip():  # Only process non-empty values
                    company_orders.append(uuid.UUID(str(oid)))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid company_orders in payload: {payload.get('company_orders', 'MISSING')} - {e}")

        return cls(
            company_id=company_id,
            client_id=client_uuid,
            owner_ids=owner_ids,
            company_industry=payload.get("company_industry"),
            client_position=payload.get("client_position"),
            company_name=payload.get("company_name"),
            company_size=payload.get("company_size"),
            company_logo=payload.get("company_logo"),
            company_description=payload.get("company_description"),
            company_orders=company_orders,
            normalized_company_name=payload.get("normalized_company_name"),
            created_at=created or datetime.utcnow(),
            updated_at=updated or datetime.utcnow(),
        )
