from __future__ import annotations

from datetime import datetime
from typing import Optional

import uuid

from ..repositories.freelancer import FreelancerRepository
from ..repositories.user import UserRepository
from ..schemas.user import (
    AvatarDownloadResponse,
    AvatarUploadResponse,
    UserResponse,
    UserUpdate,
)
from ..exceptions import BadRequestException, ConflictException, NotFoundException
from ..services.storage import FILE_SIGNED_URL_EXPIRATION_SECONDS, FirebaseStorageService
from ..utils.serialization import safe_model_dump


class UserService:
    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        freelancer_repo: Optional[FreelancerRepository] = None,
        storage_service: Optional[FirebaseStorageService] = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.freelancer_repo = freelancer_repo or FreelancerRepository()
        self.storage_service = storage_service or FirebaseStorageService()

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        return self._build_response(user)

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

        return self._build_response(updated_user)

    async def upload_avatar(
        self,
        user_id: uuid.UUID,
        content: bytes,
        content_type: Optional[str],
    ) -> AvatarUploadResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        freelancer = await self.freelancer_repo.get_by_user_id(user_id)

        if user.avatar_storage_path:
            await self.storage_service.delete_avatar(user.avatar_storage_path)
        if (
            freelancer
            and freelancer.avatar_storage_path
            and freelancer.avatar_storage_path != user.avatar_storage_path
        ):
            await self.storage_service.delete_avatar(freelancer.avatar_storage_path)

        storage_path, _ = await self.storage_service.upload_avatar(
            user_id,
            content,
            content_type,
        )
        uploaded_at = datetime.utcnow()
        avatar_update = {
            "avatar_storage_path": storage_path,
            "avatar_uploaded_at": uploaded_at.isoformat(),
            "avatar_url": None,
        }

        await self.user_repo.update(user_id, avatar_update)
        if freelancer:
            await self.freelancer_repo.update(freelancer.freelancer_id, avatar_update)

        return AvatarUploadResponse(avatar_uploaded_at=uploaded_at)

    async def delete_avatar(self, user_id: uuid.UUID) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        storage_path = user.avatar_storage_path
        freelancer = await self.freelancer_repo.get_by_user_id(user_id)
        if not storage_path and freelancer:
            storage_path = freelancer.avatar_storage_path

        if not storage_path:
            raise BadRequestException("Avatar not found")

        await self.storage_service.delete_avatar(storage_path)

        clear_payload = {
            "avatar_storage_path": None,
            "avatar_uploaded_at": None,
            "avatar_url": None,
        }
        await self.user_repo.update(user_id, clear_payload)
        if freelancer:
            await self.freelancer_repo.update(freelancer.freelancer_id, clear_payload)

    async def get_avatar_download_url(self, user_id: uuid.UUID) -> AvatarDownloadResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        freelancer = await self.freelancer_repo.get_by_user_id(user_id)
        storage_path = self._resolve_avatar_storage_path(user, freelancer)
        return await self._build_avatar_download_response(storage_path)

    async def add_role(self, user_id: uuid.UUID, role: str) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        return await self.user_repo.add_role(user_id, role)

    @staticmethod
    def _resolve_avatar_storage_path(user, freelancer) -> Optional[str]:
        if freelancer and freelancer.avatar_storage_path:
            return freelancer.avatar_storage_path
        if user and user.avatar_storage_path:
            return user.avatar_storage_path
        return None

    async def _build_avatar_download_response(
        self,
        storage_path: Optional[str],
    ) -> AvatarDownloadResponse:
        if not storage_path:
            raise BadRequestException("Avatar not found")

        download_url = await self.storage_service.generate_download_url(storage_path)
        return AvatarDownloadResponse(
            download_url=download_url,
            expires_in_seconds=FILE_SIGNED_URL_EXPIRATION_SECONDS,
        )

    @staticmethod
    def _build_response(user) -> UserResponse:
        return UserResponse(
            user_id=user.user_id,
            name=user.name,
            surname=user.surname,
            phone_number=user.phone_number,
            roles=user.roles,
            has_avatar=bool(user.avatar_storage_path),
            avatar_uploaded_at=user.avatar_uploaded_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    def avatar_payload_from_user(user) -> dict:
        payload = {"avatar_storage_path": user.avatar_storage_path}
        if user.avatar_uploaded_at:
            uploaded_at = user.avatar_uploaded_at
            payload["avatar_uploaded_at"] = (
                uploaded_at.isoformat()
                if isinstance(uploaded_at, datetime)
                else uploaded_at
            )
        return payload
