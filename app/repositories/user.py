from __future__ import annotations

import uuid
from typing import List, Optional

from .base import FirestoreRepository
from ..models.user import User


class UserRepository(FirestoreRepository[User]):
    collection_name = "users"
    id_field = "user_id"

    def __init__(self):
        super().__init__(User.from_firestore)

    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        users = await self.query(filters=[("phone_number", "==", phone_number)], limit=1)
        return users[0] if users else None

    async def create_with_roles(self, user_data: dict, roles: List[str]) -> User:
        user_id = user_data.get("user_id") or uuid.uuid4()
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        payload = {
            "user_id": str(user_id),
            "name": user_data.get("name"),
            "surname": user_data.get("surname"),
            "phone_number": user_data.get("phone_number"),
            "roles": list(dict.fromkeys(roles)),
        }
        return await self.create(payload, user_id)

    async def add_role(self, user_id: uuid.UUID, role: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        if role in user.roles:
            return False
        updated_roles = list(dict.fromkeys(user.roles + [role]))
        await self.update(user_id, {"roles": updated_roles})
        return True

    async def get_user_roles(self, user_id: uuid.UUID) -> List[str]:
        user = await self.get_by_id(user_id)
        return list(user.roles) if user else []
