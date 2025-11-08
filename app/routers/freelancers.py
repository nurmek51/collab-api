import uuid
from typing import List

from fastapi import APIRouter, Depends, Path, Query

from ..deps.auth import get_current_user, require_freelancer
from ..models.user import User
from ..schemas.common import APIResponse, PaginatedResponse
from ..schemas.freelancer import FreelancerCreate, FreelancerUpdate
from ..services.freelancer import FreelancerService

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
    try:
        freelancer_service = FreelancerService()
        freelancer = await freelancer_service.get_freelancer_by_user_id(current_user.user_id)
        updated_freelancer = await freelancer_service.update_freelancer(freelancer.freelancer_id, freelancer_update)
        return APIResponse(success=True, data=updated_freelancer)
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
