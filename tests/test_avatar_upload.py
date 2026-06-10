import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, phone_number: str = "+1234567896") -> dict:
    response = await client.post("/auth/verify-otp", json={
        "phone_number": phone_number,
        "code": "1234",
    })
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_upload_avatar_success(client: AsyncClient):
    headers = await _login(client)
    user_response = await client.get("/users/me", headers=headers)
    user_id = uuid.UUID(user_response.json()["data"]["user_id"])

    with patch("app.services.user.FirebaseStorageService") as mock_storage_cls:
        storage = mock_storage_cls.return_value
        storage.upload_avatar = AsyncMock(return_value=(
            f"avatars/users/{user_id}/avatar.jpg",
            "avatar.jpg",
        ))
        storage.generate_download_url = AsyncMock(return_value="https://signed.example/avatar.jpg")
        storage.delete_avatar = AsyncMock()

        files = {"file": ("avatar.jpg", b"\xff\xd8\xff fake jpeg", "image/jpeg")}
        response = await client.post("/users/me/avatar", headers=headers, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "avatar_uploaded_at" in data["data"]

    profile_response = await client.get("/users/me", headers=headers)
    profile = profile_response.json()["data"]
    assert profile["has_avatar"] is True


@pytest.mark.asyncio
async def test_get_avatar_download_url(client: AsyncClient):
    headers = await _login(client, phone_number="+1234567897")
    user_response = await client.get("/users/me", headers=headers)
    user_id = uuid.UUID(user_response.json()["data"]["user_id"])

    with patch("app.services.user.FirebaseStorageService") as mock_storage_cls:
        storage = mock_storage_cls.return_value
        storage.upload_avatar = AsyncMock(return_value=(
            f"avatars/users/{user_id}/avatar.jpg",
            "avatar.jpg",
        ))
        storage.generate_download_url = AsyncMock(return_value="https://signed.example/avatar.jpg")
        storage.delete_avatar = AsyncMock()

        files = {"file": ("avatar.jpg", b"\xff\xd8\xff fake jpeg", "image/jpeg")}
        await client.post("/users/me/avatar", headers=headers, files=files)

        response = await client.get("/users/me/avatar", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["download_url"] == "https://signed.example/avatar.jpg"
    assert data["data"]["expires_in_seconds"] == 3600


@pytest.mark.asyncio
async def test_delete_avatar(client: AsyncClient):
    headers = await _login(client, phone_number="+1234567800")
    user_response = await client.get("/users/me", headers=headers)
    user_id = uuid.UUID(user_response.json()["data"]["user_id"])

    with patch("app.services.user.FirebaseStorageService") as mock_storage_cls:
        storage = mock_storage_cls.return_value
        storage.upload_avatar = AsyncMock(return_value=(
            f"avatars/users/{user_id}/avatar.jpg",
            "avatar.jpg",
        ))
        storage.generate_download_url = AsyncMock(return_value="https://signed.example/avatar.jpg")
        storage.delete_avatar = AsyncMock()

        files = {"file": ("avatar.jpg", b"\xff\xd8\xff fake jpeg", "image/jpeg")}
        await client.post("/users/me/avatar", headers=headers, files=files)

        response = await client.delete("/users/me/avatar", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["deleted"] is True

    profile_response = await client.get("/users/me", headers=headers)
    profile = profile_response.json()["data"]
    assert profile["has_avatar"] is False


@pytest.mark.asyncio
async def test_upload_avatar_rejects_invalid_type(client: AsyncClient):
    headers = await _login(client, phone_number="+1234567801")

    files = {"file": ("notes.txt", b"plain text", "text/plain")}
    response = await client.post("/users/me/avatar", headers=headers, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "JPEG" in data["error"]


@pytest.mark.asyncio
async def test_get_other_user_avatar_download_url(client: AsyncClient):
    owner_headers = await _login(client, phone_number="+1234567802")
    owner_response = await client.get("/users/me", headers=owner_headers)
    owner_id = uuid.UUID(owner_response.json()["data"]["user_id"])

    viewer_headers = await _login(client, phone_number="+1234567803")

    with patch("app.services.user.FirebaseStorageService") as mock_storage_cls:
        storage = mock_storage_cls.return_value
        storage.upload_avatar = AsyncMock(return_value=(
            f"avatars/users/{owner_id}/avatar.jpg",
            "avatar.jpg",
        ))
        storage.generate_download_url = AsyncMock(return_value="https://signed.example/other-avatar.jpg")
        storage.delete_avatar = AsyncMock()

        files = {"file": ("avatar.jpg", b"\xff\xd8\xff fake jpeg", "image/jpeg")}
        await client.post("/users/me/avatar", headers=owner_headers, files=files)

        response = await client.get(f"/users/{owner_id}/avatar", headers=viewer_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["download_url"] == "https://signed.example/other-avatar.jpg"
