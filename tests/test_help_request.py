import pytest
from httpx import AsyncClient

from app.config.settings import settings


async def _login(client: AsyncClient, phone_number: str) -> dict:
    response = await client.post("/auth/verify-otp", json={
        "phone_number": phone_number,
        "code": "1234",
    })
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_only_one_pending_help_request_per_user(client: AsyncClient):
    headers = await _login(client, "+1234567810")

    first_response = await client.post("/request-help", json={
        "reason": "Need help with onboarding",
    }, headers=headers)
    assert first_response.status_code == 200
    first_data = first_response.json()
    assert first_data["success"] is True

    second_response = await client.post("/request-help", json={
        "reason": "Another issue",
    }, headers=headers)
    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data["success"] is False
    assert "pending help request" in second_data["error"].lower()


@pytest.mark.asyncio
async def test_new_help_request_allowed_after_admin_resolves(client: AsyncClient):
    user_headers = await _login(client, "+1234567811")

    create_response = await client.post("/request-help", json={
        "reason": "Initial help request",
    }, headers=user_headers)
    assert create_response.status_code == 200
    notification_id = create_response.json()["data"]["notification_id"]

    admin_headers = await _login(client, settings.admin_phone)
    resolve_response = await client.post(
        f"/admin/help-requests/{notification_id}/resolve",
        headers=admin_headers,
    )
    assert resolve_response.status_code == 200
    assert resolve_response.json()["success"] is True

    second_response = await client.post("/request-help", json={
        "reason": "Follow-up help request",
    }, headers=user_headers)
    assert second_response.status_code == 200
    assert second_response.json()["success"] is True
