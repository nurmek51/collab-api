import uuid

from fastapi import APIRouter, Depends, File, Path, UploadFile

from ..deps.auth import get_current_user
from ..models.user import User
from ..schemas.common import APIResponse
from ..schemas.user import AccountDeletionRequest, UserUpdate
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


@router.post("/me/avatar", response_model=APIResponse)
async def upload_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload or replace the user avatar (JPEG, PNG, WebP, max 2 MB)."""
    try:
        content = await file.read()
        user_service = UserService()
        avatar = await user_service.upload_avatar(
            current_user.user_id,
            content,
            file.content_type,
        )
        return APIResponse(success=True, data=avatar)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/me/avatar", response_model=APIResponse)
async def get_my_avatar_download_url(
    current_user: User = Depends(get_current_user),
):
    """Get a temporary signed download URL for the current user's avatar."""
    try:
        user_service = UserService()
        avatar = await user_service.get_avatar_download_url(current_user.user_id)
        return APIResponse(success=True, data=avatar)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.delete("/me/avatar", response_model=APIResponse)
async def delete_user_avatar(
    current_user: User = Depends(get_current_user),
):
    """Delete the current user's avatar."""
    try:
        user_service = UserService()
        await user_service.delete_avatar(current_user.user_id)
        return APIResponse(success=True, data={"deleted": True})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.delete("/me", response_model=APIResponse)
async def delete_current_user_account(
    payload: AccountDeletionRequest,
    current_user: User = Depends(get_current_user),
):
    """Permanently delete the current account and its associated marketplace data."""
    try:
        user_service = UserService()
        result = await user_service.delete_account(current_user.user_id)
        return APIResponse(success=True, data=result)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{user_id}/avatar", response_model=APIResponse)
async def get_user_avatar_download_url(
    user_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
):
    """Get a temporary signed download URL for another user's avatar."""
    try:
        user_service = UserService()
        avatar = await user_service.get_avatar_download_url(user_id)
        return APIResponse(success=True, data=avatar)
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
