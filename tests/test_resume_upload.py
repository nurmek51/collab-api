import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.config.settings import settings


async def _login(client: AsyncClient, phone_number: str = "+1234567892") -> dict:
    response = await client.post("/auth/verify-otp", json={
        "phone_number": phone_number,
        "code": "1234",
    })
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_freelancer(client: AsyncClient) -> tuple[dict, dict]:
    headers = await _login(client)

    await client.put("/users/me", json={"name": "Resume", "surname": "Tester"}, headers=headers)

    freelancer_data = {
        "iin": "987654321098",
        "city": "Astana",
        "email": "resume.tester@example.com",
        "specializations_with_levels": [
            {"specialization": "Flutter Development", "skill_level": "middle"},
        ],
        "phone_number": "+1234567892",
        "bio": "Mobile developer",
    }
    create_response = await client.post("/freelancers/profile", json=freelancer_data, headers=headers)
    assert create_response.status_code == 200
    create_data = create_response.json()
    assert create_data["success"] is True

    return headers, create_data["data"]


@pytest.mark.asyncio
async def test_upload_resume_without_freelancer_profile(client: AsyncClient):
    headers = await _login(client, phone_number="+1234567894")

    with patch("app.services.freelancer.ResumeStorageService") as mock_storage_cls:
        storage = mock_storage_cls.return_value
        storage.upload_resume = AsyncMock(side_effect=lambda user_id, content, content_type, filename: (
            f"resumes/users/{user_id}/resume.pdf",
            "my_resume.pdf",
        ))
        storage.delete_resume = AsyncMock()

        files = {"file": ("my_resume.pdf", b"%PDF-1.4 test", "application/pdf")}
        response = await client.post("/freelancers/profile/resume", headers=headers, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["resume_filename"] == "my_resume.pdf"


@pytest.mark.asyncio
async def test_upload_resume_success(client: AsyncClient):
    headers, freelancer = await _create_freelancer(client)
    user_id = uuid.UUID(freelancer["user_id"])

    with patch("app.services.freelancer.ResumeStorageService") as mock_storage_cls:
        storage = mock_storage_cls.return_value
        storage.upload_resume = AsyncMock(return_value=(
            f"resumes/users/{user_id}/resume.pdf",
            "my_resume.pdf",
        ))
        storage.generate_download_url = AsyncMock(return_value="https://signed.example/resume.pdf")
        storage.delete_resume = AsyncMock()

        files = {"file": ("my_resume.pdf", b"%PDF-1.4 test", "application/pdf")}
        response = await client.post("/freelancers/profile/resume", headers=headers, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["resume_filename"] == "my_resume.pdf"
    assert "resume_uploaded_at" in data["data"]

    profile_response = await client.get("/freelancers/profile", headers=headers)
    profile = profile_response.json()["data"]
    assert profile["has_resume"] is True
    assert profile["resume_filename"] == "my_resume.pdf"


@pytest.mark.asyncio
async def test_get_resume_download_url(client: AsyncClient):
    headers, freelancer = await _create_freelancer(client)
    user_id = uuid.UUID(freelancer["user_id"])

    with patch("app.services.freelancer.ResumeStorageService") as mock_storage_cls:
        storage = mock_storage_cls.return_value
        storage.upload_resume = AsyncMock(return_value=(
            f"resumes/users/{user_id}/resume.pdf",
            "my_resume.pdf",
        ))
        storage.generate_download_url = AsyncMock(return_value="https://signed.example/resume.pdf")
        storage.delete_resume = AsyncMock()

        files = {"file": ("my_resume.pdf", b"%PDF-1.4 test", "application/pdf")}
        await client.post("/freelancers/profile/resume", headers=headers, files=files)

        response = await client.get("/freelancers/profile/resume", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["download_url"] == "https://signed.example/resume.pdf"
    assert data["data"]["resume_filename"] == "my_resume.pdf"
    assert data["data"]["expires_in_seconds"] == 3600


@pytest.mark.asyncio
async def test_delete_resume(client: AsyncClient):
    headers, freelancer = await _create_freelancer(client)
    user_id = uuid.UUID(freelancer["user_id"])

    with patch("app.services.freelancer.ResumeStorageService") as mock_storage_cls:
        storage = mock_storage_cls.return_value
        storage.upload_resume = AsyncMock(return_value=(
            f"resumes/users/{user_id}/resume.pdf",
            "my_resume.pdf",
        ))
        storage.generate_download_url = AsyncMock(return_value="https://signed.example/resume.pdf")
        storage.delete_resume = AsyncMock()

        files = {"file": ("my_resume.pdf", b"%PDF-1.4 test", "application/pdf")}
        await client.post("/freelancers/profile/resume", headers=headers, files=files)

        response = await client.delete("/freelancers/profile/resume", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["deleted"] is True

    profile_response = await client.get("/freelancers/profile", headers=headers)
    profile = profile_response.json()["data"]
    assert profile["has_resume"] is False


@pytest.mark.asyncio
async def test_upload_resume_rejects_invalid_type(client: AsyncClient):
    headers = await _login(client, phone_number="+1234567895")

    files = {"file": ("notes.txt", b"plain text", "text/plain")}
    response = await client.post("/freelancers/profile/resume", headers=headers, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "PDF" in data["error"]


@pytest.mark.asyncio
async def test_admin_can_get_freelancer_resume_url(client: AsyncClient):
    freelancer_headers, freelancer = await _create_freelancer(client)
    user_id = uuid.UUID(freelancer["user_id"])
    freelancer_id = uuid.UUID(freelancer["freelancer_id"])

    admin_response = await client.post("/auth/verify-otp", json={
        "phone_number": settings.admin_phone,
        "code": "1234",
    })
    admin_token = admin_response.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    await client.put("/users/me", json={"name": "Admin", "surname": "Resume"}, headers=admin_headers)

    with patch("app.services.freelancer.ResumeStorageService") as mock_storage_cls:
        storage = mock_storage_cls.return_value
        storage.upload_resume = AsyncMock(return_value=(
            f"resumes/users/{user_id}/resume.pdf",
            "my_resume.pdf",
        ))
        storage.generate_download_url = AsyncMock(return_value="https://signed.example/admin-resume.pdf")
        storage.delete_resume = AsyncMock()

        files = {"file": ("my_resume.pdf", b"%PDF-1.4 test", "application/pdf")}
        await client.post("/freelancers/profile/resume", headers=freelancer_headers, files=files)

        response = await client.get(
            f"/admin/freelancers/{freelancer_id}/resume",
            headers=admin_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["download_url"] == "https://signed.example/admin-resume.pdf"
