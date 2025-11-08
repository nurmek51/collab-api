import uuid

from fastapi import APIRouter, Depends, Path

from ..deps.auth import get_current_user
from ..models.user import User
from ..schemas.common import APIResponse
from ..schemas.user import UserUpdate
from ..services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=APIResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    try:
        user_service = UserService()
        user_info = await user_service.get_user(current_user.user_id)
        return APIResponse(success=True, data=user_info)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.put("/me", response_model=APIResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
):
    try:
        user_service = UserService()
        updated_user = await user_service.update_user(current_user.user_id, user_update)
        return APIResponse(success=True, data=updated_user)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{user_id}", response_model=APIResponse)
async def get_user_by_id(
    user_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
):
    """Get user by ID"""
    try:
        user_service = UserService()
        user_info = await user_service.get_user(user_id)
        return APIResponse(success=True, data=user_info)
    except Exception as e:
        return APIResponse(success=False, error=str(e))
