from typing import Optional

import uuid

from ..repositories.user import UserRepository
from ..schemas.user import UserUpdate, UserResponse
from ..exceptions import NotFoundException, ConflictException
from ..utils.serialization import safe_model_dump


class UserService:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    async def get_user(self, user_id: uuid.UUID) -> Optional[UserResponse]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        return UserResponse(
            user_id=user.user_id,
            name=user.name,
            surname=user.surname,
            phone_number=user.phone_number,
            roles=user.roles,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def update_user(self, user_id: uuid.UUID, user_update: UserUpdate) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        update_data = safe_model_dump(user_update, exclude_unset=True)

        if "phone_number" in update_data:
            existing_user = await self.user_repo.get_by_phone(update_data["phone_number"])
            if existing_user and existing_user.user_id != user_id:
                raise ConflictException("Phone number already exists")

        updated_user = await self.user_repo.update(user_id, update_data)
        if not updated_user:
            raise NotFoundException("User not found")

        return await self.get_user(user_id)

    async def add_role(self, user_id: uuid.UUID, role: str) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        return await self.user_repo.add_role(user_id, role)
