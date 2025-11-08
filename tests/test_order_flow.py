import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_order_creation_and_application_flow(client: AsyncClient):
    # Step 1: Create client user
    client_response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567892",
        "code": "1234"
    })
    client_token = client_response.json()["data"]["access_token"]
    client_headers = {"Authorization": f"Bearer {client_token}"}
    
    # Step 2: Create order
    order_data = {
        "name": "Client",
        "surname": "User",
        "company_name": "Tech Corp",
        "company_position": "CTO",
        "order_description": "Need a senior Python developer for 3 months",
        "order_title": "Python Developer Position",
        "order_specializations": [
            {"specialization": "Python Development", "skill_level": "senior", "vacancy_id": "550e8400-e29b-41d4-a716-446655440002"},
            {"specialization": "FastAPI", "skill_level": "middle", "vacancy_id": "550e8400-e29b-41d4-a716-446655440003"},
        ],
        "requirements": "3+ years experience required"
    }
    
    response = await client.post("/orders/create", json=order_data, headers=client_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    order_id = data["data"]["order_id"]
    assert data["data"]["order_status"] == "pending"
    
    # Step 3: Create admin and approve order
    admin_response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567899",
        "code": "1234"
    })
    admin_token = admin_response.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    await client.put("/users/me", json={
        "name": "Admin",
        "surname": "User"
    }, headers=admin_headers)
    
    admin_role_response = await client.post("/auth/select-role", json={
        "role": "admin"
    }, headers=admin_headers)
    assert admin_role_response.status_code == 200
    assert admin_role_response.json()["success"] is True
    
    # Complete order (approve)
    response = await client.post(f"/admin/orders/{order_id}/complete", json={
        "order_description": "Updated description with more details",
        "requirements": "Updated requirements"
    }, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["order_status"] == "approved"
    
    # Step 4: Create freelancer and apply to order
    freelancer_response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567893",
        "code": "1234"
    })
    freelancer_token = freelancer_response.json()["data"]["access_token"]
    freelancer_headers = {"Authorization": f"Bearer {freelancer_token}"}
    
    await client.put("/users/me", json={
        "name": "Freelancer",
        "surname": "Dev"
    }, headers=freelancer_headers)
    
    await client.post("/auth/select-role", json={
        "role": "freelancer"
    }, headers=freelancer_headers)
    
    # Create freelancer profile
    freelancer_data = {
        "iin": "123456789013",
        "city": "Almaty",
        "email": "freelancer@example.com",
        "specializations_with_levels": [
            {"specialization": "Python Development", "skill_level": "senior"}
        ],
        "experience_description": "Senior Python developer",
        "phone_number": "+1234567893"
    }
    
    response = await client.post("/freelancers/profile", json=freelancer_data, headers=freelancer_headers)
    freelancer_id = response.json()["data"]["freelancer_id"]
    
    # Approve freelancer
    await client.put(f"/admin/freelancers/{freelancer_id}/approve", json={
        "status": "approved"
    }, headers=admin_headers)
    
    # Apply to order
    response = await client.post("/applications/", json={
        "order_id": order_id,
        "freelancer_id": freelancer_id
    }, headers=freelancer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    application_id = data["data"]["id"]
    
    # Step 5: Client accepts application
    response = await client.put(f"/applications/{application_id}", json={
        "status": "accepted"
    }, headers=client_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "accepted"
