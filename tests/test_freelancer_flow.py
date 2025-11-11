import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_freelancer_creation_and_approval_flow(client: AsyncClient):
    # Step 1: Login and get token
    response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567891",
        "code": "1234"
    })
    token = response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Update user info first
    await client.put("/users/me", json={
        "name": "John",
        "surname": "Doe"
    }, headers=headers)
    
    # Step 3: Select freelancer role
    role_response = await client.post("/auth/select-role", json={
        "role": "freelancer"
    }, headers=headers)
    assert role_response.status_code == 200
    data = role_response.json()
    assert data["success"] is True or (data["success"] is False and data.get("error") == "Role already exists")
    
    # Step 4: Create freelancer profile
    freelancer_data = {
        "iin": "123456789012",
        "city": "Almaty",
        "email": "john@example.com",
        "specializations_with_levels": [
            {"specialization": "Python Development", "skill_level": "senior"},
            {"specialization": "React Development", "skill_level": "middle"}
        ],
        "phone_number": "+1234567891",
        "bio": "Experienced developer"
    }
    
    response = await client.post("/freelancers/profile", json=freelancer_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    if data["success"] is False:
        assert "already exists" in data.get("error", "")
        # Get existing freelancer
        get_response = await client.get("/freelancers/profile", headers=headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["success"] is True
        freelancer_id = get_data["data"]["freelancer_id"]
        assert get_data["data"]["status"] in ["pending", "approved"]
    else:
        freelancer_id = data["data"]["freelancer_id"]
        assert data["data"]["status"] == "pending"
    
    # Step 5: Create admin user and approve freelancer
    admin_response = await client.post("/auth/verify-otp", json={
        "phone_number": "+1234567899",
        "code": "1234"
    })
    admin_token = admin_response.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Update admin user info and role
    await client.put("/users/me", json={
        "name": "Admin",
        "surname": "User"
    }, headers=admin_headers)
    
    admin_role_response = await client.post("/auth/select-role", json={
        "role": "admin"
    }, headers=admin_headers)
    assert admin_role_response.status_code == 200
    assert admin_role_response.json()["success"] is True
    
    # Approve freelancer
    response = await client.put(f"/admin/freelancers/{freelancer_id}/approve", json={
        "status": "approved"
    }, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "approved"
