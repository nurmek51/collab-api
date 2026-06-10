import pytest
from httpx import AsyncClient


async def _client_headers(client: AsyncClient, phone_number: str) -> dict:
    response = await client.post("/auth/verify-otp", json={
        "phone_number": phone_number,
        "code": "1234",
    })
    token = response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    await client.put("/users/me", json={"name": "Client", "surname": "User"}, headers=headers)
    await client.post("/auth/select-role", json={"role": "client"}, headers=headers)
    await client.post("/clients/profile", json={}, headers=headers)
    return headers


@pytest.mark.asyncio
async def test_duplicate_company_names_are_allowed(client: AsyncClient):
    headers = await _client_headers(client, "+1234567812")

    first_company = await client.post("/companies/", json={
        "company_name": "Acme Corp",
    }, headers=headers)
    assert first_company.status_code == 200
    assert first_company.json()["success"] is True

    second_company = await client.post("/companies/", json={
        "company_name": "Acme Corp",
    }, headers=headers)
    assert second_company.status_code == 200
    second_data = second_company.json()
    assert second_data["success"] is True
    assert (
        second_data["data"]["company_id"]
        != first_company.json()["data"]["company_id"]
    )
