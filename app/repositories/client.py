from __future__ import annotations

import uuid
from typing import Optional

from .base import FirestoreRepository
from ..models.client import Client


class ClientRepository(FirestoreRepository[Client]):
    collection_name = "clients"
    id_field = "client_id"

    def __init__(self):
        super().__init__(Client.from_firestore)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Client]:
        clients = await self.query(filters=[("user_id", "==", str(user_id))], limit=1)
        return clients[0] if clients else None

    async def add_company(self, client_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Client]:
        client = await self.get_by_id(client_id)
        if not client:
            return None
        company_ids = list({*client.company_ids, company_id})
        await self.update(client_id, {"company_ids": [str(cid) for cid in company_ids]})
        return await self.get_by_id(client_id)
