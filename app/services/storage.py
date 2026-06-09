from __future__ import annotations

import asyncio
import uuid
from datetime import timedelta
from typing import Optional

from firebase_admin import storage

from ..config.firebase import initialize_firebase
from ..config.settings import settings
from ..exceptions import BadRequestException

ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024
RESUME_SIGNED_URL_EXPIRATION_SECONDS = 3600


class ResumeStorageService:
    def __init__(self, bucket_name: Optional[str] = None) -> None:
        self._bucket_name = bucket_name or settings.firebase_storage_bucket

    def _get_bucket(self):
        app = initialize_firebase()
        if not app:
            raise BadRequestException("File storage is not configured")
        if not self._bucket_name:
            raise BadRequestException("Storage bucket is not configured")
        return storage.bucket(self._bucket_name)

    @staticmethod
    def build_resume_path(freelancer_id: uuid.UUID, extension: str) -> str:
        return f"resumes/{freelancer_id}/resume.{extension}"

    def _validate_resume(self, content: bytes, content_type: Optional[str]) -> str:
        if not content:
            raise BadRequestException("Resume file is empty")

        if len(content) > MAX_RESUME_SIZE_BYTES:
            raise BadRequestException("Resume file must be 5 MB or smaller")

        normalized_type = (content_type or "").split(";")[0].strip().lower()
        extension = ALLOWED_CONTENT_TYPES.get(normalized_type)
        if not extension:
            raise BadRequestException("Resume must be a PDF, DOC, or DOCX file")

        return extension

    async def upload_resume(
        self,
        freelancer_id: uuid.UUID,
        content: bytes,
        content_type: Optional[str],
        original_filename: Optional[str],
    ) -> tuple[str, str]:
        extension = self._validate_resume(content, content_type)
        storage_path = self.build_resume_path(freelancer_id, extension)

        def _upload() -> None:
            bucket = self._get_bucket()
            blob = bucket.blob(storage_path)
            blob.upload_from_string(
                content,
                content_type=(content_type or "").split(";")[0].strip().lower(),
            )

        await asyncio.to_thread(_upload)
        filename = original_filename or f"resume.{extension}"
        return storage_path, filename

    async def delete_resume(self, storage_path: str) -> None:
        def _delete() -> None:
            bucket = self._get_bucket()
            blob = bucket.blob(storage_path)
            if blob.exists():
                blob.delete()

        await asyncio.to_thread(_delete)

    async def generate_download_url(self, storage_path: str) -> str:
        def _generate() -> str:
            bucket = self._get_bucket()
            blob = bucket.blob(storage_path)
            if not blob.exists():
                raise BadRequestException("Resume file not found in storage")
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=RESUME_SIGNED_URL_EXPIRATION_SECONDS),
                method="GET",
            )

        return await asyncio.to_thread(_generate)
