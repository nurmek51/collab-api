import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_request_otp(client: AsyncClient, mock_twilio):
    response = await client.post("/auth/request-otp", json={
        "phone_number": "+1234567890"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_verify_otp_success(client: AsyncClient, mock_twilio):
    response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567890",
        "code": "1234"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

@pytest.mark.asyncio
async def test_verify_otp_failure(client: AsyncClient, mock_twilio):
    mock_twilio.verify_otp.return_value = False
    response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567890",
        "code": "0000"
    })
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_select_role_unauthorized(client: AsyncClient):
    response = await client.post("/auth/select-role", json={
        "role": "freelancer"
    })
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_full_auth_flow(client: AsyncClient, mock_twilio):
    # Verify OTP and get token
    response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567890",
        "code": "1234"
    })
    assert response.status_code == 200
    token_data = response.json()
    token = token_data["data"]["access_token"]
    
    # Select role with token
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/auth/select-role", json={
        "role": "freelancer"
    }, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient, mock_twilio):
    login_response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567890",
        "code": "1234"
    })
    assert login_response.status_code == 200
    login_data = login_response.json()["data"]

    refresh_response = await client.post("/auth/refresh", json={
        "refresh_token": login_data["refresh_token"]
    })
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()["data"]

    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    assert refresh_data["access_token"] != login_data["access_token"]
    assert refresh_data["refresh_token"] != login_data["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_failure_with_access_token(client: AsyncClient, mock_twilio):
    login_response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567890",
        "code": "1234"
    })
    assert login_response.status_code == 200
    access_token = login_response.json()["data"]["access_token"]

    refresh_response = await client.post("/auth/refresh", json={
        "refresh_token": access_token
    })
    assert refresh_response.status_code == 400
