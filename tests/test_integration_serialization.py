"""Integration tests that validate Firestore serialization paths."""

import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, phone: str) -> dict:
    response = await client.post(
        "/auth/verify-otp",
        json={"phone_number": phone, "code": "1234"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_freelancer_profile_serialization(client: AsyncClient):
    headers = await _auth_headers(client, "+77000000001")
    role_response = await client.post("/auth/select-role", json={"role": "freelancer"}, headers=headers)
    assert role_response.status_code == 200
    assert role_response.json()["success"] is True

    payload = {
        "iin": "123456789012",
        "city": "Almaty",
        "email": "freelancer@example.com",
        "specializations_with_levels": [
            {"specialization": "fullstack", "skill_level": "junior"},
            {"specialization": "backend", "skill_level": "middle"},
        ],
        "experience_description": "Experienced developer",
        "payment_info": {"bank_account": "1234567890", "payment_method": "bank_transfer"},
        "social_links": {"linkedin": "https://linkedin.com/in/test"},
        "portfolio_links": {"portfolio": "https://portfolio.com"},
        "bio": "Passionate developer",
    }

    response = await client.post("/freelancers/profile", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "freelancer@example.com"
    assert len(data["specializations_with_levels"]) == 2
    assert data["payment_info"]["payment_method"] == "bank_transfer"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_duplicate_freelancer_email_rejected(client: AsyncClient):
    first_headers = await _auth_headers(client, "+77000000002")
    first_role = await client.post("/auth/select-role", json={"role": "freelancer"}, headers=first_headers)
    assert first_role.status_code == 200

    payload = {
        "iin": "111111111111",
        "city": "Astana",
        "email": "duplicate@example.com",
        "specializations_with_levels": [
            {"specialization": "design", "skill_level": "middle"}
        ],
        "experience_description": "Design experience",
    }

    create_response = await client.post("/freelancers/profile", json=payload, headers=first_headers)
    assert create_response.status_code == 200
    assert create_response.json()["success"] is True

    second_headers = await _auth_headers(client, "+77000000003")
    second_role = await client.post("/auth/select-role", json={"role": "freelancer"}, headers=second_headers)
    assert second_role.status_code == 200
    dup_response = await client.post("/freelancers/profile", json=payload, headers=second_headers)
    assert dup_response.status_code == 200
    dup_json = dup_response.json()
    assert dup_json["success"] is False
    assert "Email" in dup_json["error"]


@pytest.mark.asyncio
async def test_create_order_with_nested_payload(client: AsyncClient):
    headers = await _auth_headers(client, "+77000000004")
    role_response = await client.post("/auth/select-role", json={"role": "client"}, headers=headers)
    assert role_response.status_code == 200
    assert role_response.json()["success"] is True

    order_payload = {
        "order_title": "E-commerce Development",
        "order_description": "Need a full-stack developer",
        "order_condition": {
            "salary": 150000.0,
            "pay_per": "month",
            "required_experience": 3,
            "schedule_type": "full-time",
            "format_type": "remote",
        },
        "requirements": "React, Node.js",
        "chat_link": "https://t.me/project_chat",
        "contracts": {"contract_type": "employment", "duration_months": 12},
        "order_specializations": [
            {"specialization": "fullstack", "skill_level": "senior", "vacancy_id": "550e8400-e29b-41d4-a716-446655440000"},
            {"specialization": "frontend", "skill_level": "middle", "vacancy_id": "550e8400-e29b-41d4-a716-446655440001"},
        ],
        "name": "Client",
        "surname": "Owner",
        "company_name": "Tech Corp",
        "company_position": "CTO",
    }

    response = await client.post("/orders/create", json=order_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["order_title"] == "E-commerce Development"
    assert data["order_condition"]["schedule_type"] == "full-time"
    assert data["contracts"]["duration_months"] == 12
    specializations = data["order_specializations"]
    assert isinstance(specializations, list)
    assert {spec["specialization"] for spec in specializations} == {"fullstack", "frontend"}

