import pytest
from httpx import AsyncClient

from app.repositories.notification import NotificationRepository


async def _login(client: AsyncClient, phone_number: str = "+1234567888") -> dict:
    response = await client.post(
        "/auth/verify-otp",
        json={"phone_number": phone_number, "code": "1234"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.mark.asyncio
async def test_delete_current_account(client: AsyncClient):
    headers = await _login(client)

    response = await client.request(
        "DELETE", "/users/me", headers=headers, json={"confirm": True}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["deleted"] is True
    assert payload["data"]["deleted_resources"] == {
        "user": 1,
        "freelancer_profiles": 0,
        "client_profiles": 0,
        "companies": 0,
        "orders": 0,
        "order_applications": 0,
        "notifications": 0,
        "files": 0,
    }

    assert (await client.get("/users/me", headers=headers)).status_code == 401


@pytest.mark.asyncio
async def test_delete_current_account_requires_confirmation(client: AsyncClient):
    headers = await _login(client, "+1234567889")

    response = await client.request(
        "DELETE", "/users/me", headers=headers, json={"confirm": False}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_account_removes_notifications_without_sort_index(client: AsyncClient):
    headers = await _login(client, "+1234567891")
    profile = (await client.get("/users/me", headers=headers)).json()["data"]
    user_id = profile["user_id"]
    notifications = NotificationRepository()
    await notifications.create({
        "type": "user_action",
        "status": "pending",
        "title": "Test notification",
        "message": "Must be removed with the account",
        "user_id": user_id,
    })

    response = await client.request(
        "DELETE", "/users/me", headers=headers, json={"confirm": True}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["deleted_resources"]["notifications"] == 1
