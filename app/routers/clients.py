import uuid

from fastapi import APIRouter, Depends, Path

from ..deps.auth import get_current_user, require_client
from ..models.user import User
from ..schemas.client import ClientCreate, ClientUpdate
from ..schemas.common import APIResponse
from ..services.client import ClientService

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("/profile", response_model=APIResponse)
async def create_client_profile(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
):
    try:
        client_service = ClientService()
        client = await client_service.create_client_profile(current_user.user_id, client_data)
        return APIResponse(success=True, data=client)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/profile", response_model=APIResponse)
async def get_my_client_profile(
    current_user: User = Depends(require_client()),
):
    try:
        client_service = ClientService()
        client = await client_service.get_client_by_user_id(current_user.user_id)
        return APIResponse(success=True, data=client)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.put("/profile", response_model=APIResponse)
async def update_client_profile(
    client_update: ClientUpdate,
    current_user: User = Depends(require_client()),
):
    try:
        client_service = ClientService()
        client = await client_service.get_client_by_user_id(current_user.user_id)
        updated_client = await client_service.update_client(client.client_id, client_update)
        return APIResponse(success=True, data=updated_client)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{client_id}", response_model=APIResponse)
async def get_client_by_id(
    client_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
):
    """Get client profile by ID"""
    try:
        client_service = ClientService()
        client = await client_service.get_client_by_id(client_id)
        return APIResponse(success=True, data=client)
    except Exception as e:
        return APIResponse(success=False, error=str(e))
