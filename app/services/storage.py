from __future__ import annotations

import asyncio
import uuid
from datetime import timedelta
from typing import Optional

from firebase_admin import storage

from ..config.firebase import initialize_firebase
from ..config.settings import settings
from ..exceptions import BadRequestException

ALLOWED_RESUME_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

ALLOWED_AVATAR_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024
MAX_AVATAR_SIZE_BYTES = 2 * 1024 * 1024
FILE_SIGNED_URL_EXPIRATION_SECONDS = 3600
RESUME_SIGNED_URL_EXPIRATION_SECONDS = FILE_SIGNED_URL_EXPIRATION_SECONDS


def _storage_error_message(exc: Exception) -> str:
    message = str(exc)
    if "403" in message or "storage.objects" in message or "Permission" in message:
        project = settings.firebase_project_id or "your Firebase project"
        bucket = settings.resolved_firebase_storage_bucket or "your storage bucket"
        return (
            f"Storage permission denied for bucket '{bucket}'. "
            f"Cloud Run must use a service account from project '{project}' "
            "(update FIREBASE_CREDENTIALS_JSON) with role Storage Object Admin."
        )
    return f"Storage operation failed: {message}"


class FirebaseStorageService:
    def __init__(self, bucket_name: Optional[str] = None) -> None:
        self._bucket_name = bucket_name or settings.resolved_firebase_storage_bucket

    def _get_bucket(self):
        app = initialize_firebase()
        if not app:
            raise BadRequestException("File storage is not configured")
        if not self._bucket_name:
            raise BadRequestException("Storage bucket is not configured")
        return storage.bucket(self._bucket_name)

    @staticmethod
    def build_resume_path(user_id: uuid.UUID, extension: str) -> str:
        return f"resumes/users/{user_id}/resume.{extension}"

    @staticmethod
    def build_avatar_path(user_id: uuid.UUID, extension: str) -> str:
        return f"avatars/users/{user_id}/avatar.{extension}"

    @staticmethod
    def _normalize_content_type(content_type: Optional[str]) -> str:
        return (content_type or "").split(";")[0].strip().lower()

    def _validate_file(
        self,
        content: bytes,
        content_type: Optional[str],
        allowed_types: dict[str, str],
        max_size_bytes: int,
        empty_message: str,
        size_message: str,
        type_message: str,
    ) -> str:
        if not content:
            raise BadRequestException(empty_message)

        if len(content) > max_size_bytes:
            raise BadRequestException(size_message)

        normalized_type = self._normalize_content_type(content_type)
        extension = allowed_types.get(normalized_type)
        if not extension:
            raise BadRequestException(type_message)

        return extension

    def _validate_resume(self, content: bytes, content_type: Optional[str]) -> str:
        return self._validate_file(
            content,
            content_type,
            ALLOWED_RESUME_CONTENT_TYPES,
            MAX_RESUME_SIZE_BYTES,
            "Resume file is empty",
            "Resume file must be 5 MB or smaller",
            "Resume must be a PDF, DOC, or DOCX file",
        )

    def _validate_avatar(self, content: bytes, content_type: Optional[str]) -> str:
        return self._validate_file(
            content,
            content_type,
            ALLOWED_AVATAR_CONTENT_TYPES,
            MAX_AVATAR_SIZE_BYTES,
            "Avatar file is empty",
            "Avatar file must be 2 MB or smaller",
            "Avatar must be a JPEG, PNG, or WebP image",
        )

    async def upload_resume(
        self,
        user_id: uuid.UUID,
        content: bytes,
        content_type: Optional[str],
        original_filename: Optional[str],
    ) -> tuple[str, str]:
        extension = self._validate_resume(content, content_type)
        storage_path = self.build_resume_path(user_id, extension)

        def _upload() -> None:
            try:
                bucket = self._get_bucket()
                blob = bucket.blob(storage_path)
                blob.upload_from_string(
                    content,
                    content_type=self._normalize_content_type(content_type),
                )
            except Exception as exc:
                raise BadRequestException(_storage_error_message(exc)) from exc

        await asyncio.to_thread(_upload)
        filename = original_filename or f"resume.{extension}"
        return storage_path, filename

    async def upload_avatar(
        self,
        user_id: uuid.UUID,
        content: bytes,
        content_type: Optional[str],
    ) -> tuple[str, str]:
        extension = self._validate_avatar(content, content_type)
        storage_path = self.build_avatar_path(user_id, extension)

        def _upload() -> None:
            try:
                bucket = self._get_bucket()
                blob = bucket.blob(storage_path)
                blob.upload_from_string(
                    content,
                    content_type=self._normalize_content_type(content_type),
                )
            except Exception as exc:
                raise BadRequestException(_storage_error_message(exc)) from exc

        await asyncio.to_thread(_upload)
        return storage_path, f"avatar.{extension}"

    async def delete_file(self, storage_path: str) -> None:
        def _delete() -> None:
            try:
                bucket = self._get_bucket()
                blob = bucket.blob(storage_path)
                if blob.exists():
                    blob.delete()
            except Exception as exc:
                raise BadRequestException(_storage_error_message(exc)) from exc

        await asyncio.to_thread(_delete)

    async def delete_resume(self, storage_path: str) -> None:
        await self.delete_file(storage_path)

    async def delete_avatar(self, storage_path: str) -> None:
        await self.delete_file(storage_path)

    async def generate_download_url(self, storage_path: str) -> str:
        def _generate() -> str:
            try:
                bucket = self._get_bucket()
                blob = bucket.blob(storage_path)
                if not blob.exists():
                    raise BadRequestException("File not found in storage")
                return blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(seconds=FILE_SIGNED_URL_EXPIRATION_SECONDS),
                    method="GET",
                )
            except BadRequestException:
                raise
            except Exception as exc:
                raise BadRequestException(_storage_error_message(exc)) from exc

        return await asyncio.to_thread(_generate)


# Backward-compatible alias
ResumeStorageService = FirebaseStorageService
