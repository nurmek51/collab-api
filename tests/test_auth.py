import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_request_otp(client: AsyncClient):
    response = await client.post("/auth/request-otp", json={
        "phone_number": "+1234567890"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_verify_otp_success(client: AsyncClient):
    response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567890",
        "code": "1234"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]

@pytest.mark.asyncio
async def test_verify_otp_failure(client: AsyncClient):
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
async def test_full_auth_flow(client: AsyncClient):
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
