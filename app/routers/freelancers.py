import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from pydantic import ValidationError

from ..deps.auth import get_current_user, require_freelancer
from ..models.user import User
from ..schemas.common import APIResponse, PaginatedResponse
from ..schemas.freelancer import FreelancerCreate, FreelancerUpdate
from ..services.freelancer import FreelancerService
from ..exceptions import NotFoundException

router = APIRouter(prefix="/freelancers", tags=["Freelancers"])


@router.post("/profile", response_model=APIResponse)
async def create_freelancer_profile(
    freelancer_data: FreelancerCreate,
    current_user: User = Depends(get_current_user),
):
    try:
        freelancer_service = FreelancerService()
        freelancer = await freelancer_service.create_freelancer_profile(current_user.user_id, freelancer_data)
        return APIResponse(success=True, data=freelancer)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/profile", response_model=APIResponse)
async def get_my_freelancer_profile(
    current_user: User = Depends(require_freelancer()),
):
    try:
        freelancer_service = FreelancerService()
        freelancer = await freelancer_service.get_freelancer_by_user_id(current_user.user_id)
        return APIResponse(success=True, data=freelancer)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.put("/profile", response_model=APIResponse)
async def update_freelancer_profile(
    freelancer_update: FreelancerUpdate,
    current_user: User = Depends(require_freelancer()),
):
    """Update a freelancer profile, creating it for legacy onboarding clients.

    The documented create operation remains ``POST /freelancers/profile``.  Some
    released clients send their first, complete profile payload to this PUT
    endpoint after choosing the freelancer role.  Treat that request as an
    upsert so those clients do not become stuck with a missing profile.
    """
    try:
        freelancer_service = FreelancerService()
        try:
            freelancer = await freelancer_service.get_freelancer_by_user_id(current_user.user_id)
        except NotFoundException:
            try:
                create_data = FreelancerCreate.model_validate(
                    freelancer_update.model_dump(by_alias=True, exclude_unset=True)
                )
            except ValidationError as exc:
                raise HTTPException(
                    status_code=422,
                    detail="A complete freelancer profile is required for initial creation",
                ) from exc
            created_freelancer = await freelancer_service.create_freelancer_profile(
                current_user.user_id,
                create_data,
            )
            return APIResponse(success=True, data=created_freelancer)

        updated_freelancer = await freelancer_service.update_freelancer(
            freelancer.freelancer_id,
            freelancer_update,
        )
        return APIResponse(success=True, data=updated_freelancer)
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/profile/resume", response_model=APIResponse)
async def upload_freelancer_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload or replace the freelancer resume (PDF, DOC, DOCX, max 5 MB)."""
    try:
        content = await file.read()
        freelancer_service = FreelancerService()
        resume = await freelancer_service.upload_resume(
            current_user.user_id,
            content,
            file.content_type,
            file.filename,
        )
        return APIResponse(success=True, data=resume)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/profile/resume", response_model=APIResponse)
async def get_my_freelancer_resume_download_url(
    current_user: User = Depends(get_current_user),
):
    """Get a temporary signed download URL for the current freelancer's resume."""
    try:
        freelancer_service = FreelancerService()
        resume = await freelancer_service.get_resume_download_url_for_user(current_user.user_id)
        return APIResponse(success=True, data=resume)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.delete("/profile/resume", response_model=APIResponse)
async def delete_freelancer_resume(
    current_user: User = Depends(get_current_user),
):
    """Delete the current freelancer's resume."""
    try:
        freelancer_service = FreelancerService()
        await freelancer_service.delete_resume(current_user.user_id)
        return APIResponse(success=True, data={"deleted": True})
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/", response_model=APIResponse)
async def get_approved_freelancers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    try:
        freelancer_service = FreelancerService()
        skip = (page - 1) * size
        freelancers = await freelancer_service.get_approved_freelancers(skip, size)
        
        paginated_response = PaginatedResponse(
            items=freelancers,
            total=len(freelancers),
            page=page,
            size=size,
            pages=(len(freelancers) + size - 1) // size
        )
        return APIResponse(success=True, data=paginated_response)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{freelancer_id}", response_model=APIResponse)
async def get_freelancer_by_id(
    freelancer_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
):
    """Get freelancer profile by ID"""
    try:
        freelancer_service = FreelancerService()
        freelancer = await freelancer_service.get_freelancer_by_id(freelancer_id)
        return APIResponse(success=True, data=freelancer)
    except Exception as e:
        return APIResponse(success=False, error=str(e))
