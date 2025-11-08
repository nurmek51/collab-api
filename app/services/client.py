from __future__ import annotations

import uuid
from typing import Optional

from ..repositories.client import ClientRepository
from ..repositories.user import UserRepository
from ..schemas.client import ClientCreate, ClientUpdate, ClientResponse
from ..exceptions import NotFoundException, ConflictException
from ..utils.serialization import safe_model_dump


class ClientService:
    def __init__(self, client_repo: Optional[ClientRepository] = None, user_repo: Optional[UserRepository] = None):
        self.client_repo = client_repo or ClientRepository()
        self.user_repo = user_repo or UserRepository()

    async def create_client_profile(self, user_id: uuid.UUID, client_data: ClientCreate) -> ClientResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        existing_client = await self.client_repo.get_by_user_id(user_id)
        if existing_client:
            raise ConflictException("Client profile already exists")

        client = await self.client_repo.create({
            "user_id": str(user_id),
            "company_ids": [],
        })

        update_data = safe_model_dump(client_data, exclude_unset=True)
        if update_data:
            await self.user_repo.update(user_id, update_data)

        await self.user_repo.add_role(user_id, "client")

        return await self._build_response(client)

    async def get_client(self, client_id: uuid.UUID) -> ClientResponse:
        client = await self.client_repo.get_by_id(client_id)
        if not client:
            raise NotFoundException("Client not found")
        return await self._build_response(client)

    async def get_client_by_user_id(self, user_id: uuid.UUID) -> ClientResponse:
        client = await self.client_repo.get_by_user_id(user_id)
        if not client:
            raise NotFoundException("Client profile not found")
        return await self._build_response(client)

    async def get_client_by_id(self, client_id: uuid.UUID) -> ClientResponse:
        return await self.get_client(client_id)

    async def update_client(self, client_id: uuid.UUID, client_update: ClientUpdate) -> ClientResponse:
        client = await self.client_repo.get_by_id(client_id)
        if not client:
            raise NotFoundException("Client not found")

        update_data = safe_model_dump(client_update, exclude_unset=True)
        if update_data:
            await self.user_repo.update(client.user_id, update_data)

        refreshed = await self.client_repo.get_by_id(client_id)
        if not refreshed:
            raise NotFoundException("Client not found")
        return await self._build_response(refreshed)

    async def _build_response(self, client) -> ClientResponse:
        user = await self.user_repo.get_by_id(client.user_id)
        if not user:
            raise NotFoundException("User not found")

        return ClientResponse(
            client_id=client.client_id,
            user_id=client.user_id,
            name=user.name,
            surname=user.surname,
            phone_number=user.phone_number,
            company_ids=client.company_ids,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )
