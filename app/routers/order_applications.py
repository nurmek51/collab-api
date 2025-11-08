import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Path

from ..deps.auth import get_current_user, require_client, require_freelancer
from ..models.user import User
from ..schemas.common import APIResponse
from ..schemas.order_application import OrderApplicationCreate, OrderApplicationUpdate
from ..services.freelancer import FreelancerService
from ..services.order_application import OrderApplicationService

router = APIRouter(prefix="/applications", tags=["Order Applications"])


@router.post("/", response_model=APIResponse)
async def create_application(
    application_data: OrderApplicationCreate,
    current_user: User = Depends(require_freelancer()),
):
    try:
        freelancer_service = FreelancerService()
        application_service = OrderApplicationService()
        freelancer = await freelancer_service.get_freelancer_by_user_id(current_user.user_id)
        application = await application_service.create_application(freelancer.freelancer_id, application_data)
        return APIResponse(success=True, data=application)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/my", response_model=APIResponse)
async def get_my_applications(
    current_user: User = Depends(require_freelancer()),
):
    try:
        freelancer_service = FreelancerService()
        application_service = OrderApplicationService()
        freelancer = await freelancer_service.get_freelancer_by_user_id(current_user.user_id)
        applications = await application_service.get_applications_by_freelancer(freelancer.freelancer_id)
        return APIResponse(success=True, data=applications)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/order/{order_id}", response_model=APIResponse)
async def get_order_applications(
    order_id: uuid.UUID = Path(...),
    current_user: User = Depends(require_client()),
):
    try:
        application_service = OrderApplicationService()
        applications = await application_service.get_applications_by_order(order_id)
        return APIResponse(success=True, data=applications)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.put("/{application_id}", response_model=APIResponse)
async def update_application_status(
    application_id: uuid.UUID = Path(...),
    status_update: OrderApplicationUpdate = ...,
    current_user: User = Depends(require_client()),
):
    try:
        application_service = OrderApplicationService()
        updated_application = await application_service.update_application_status(application_id, status_update)
        return APIResponse(success=True, data=updated_application)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/order/{order_id}/available-specializations", response_model=APIResponse)
async def get_available_specializations(
    order_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
):
    """Get available (non-occupied) specializations for an order"""
    try:
        application_service = OrderApplicationService()
        specializations = await application_service.get_available_specializations(order_id)
        return APIResponse(success=True, data=specializations)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/order/{order_id}/specialization/{specialization_index}", response_model=APIResponse)
async def get_applications_by_specialization(
    order_id: uuid.UUID = Path(...),
    specialization_index: int = Path(...),
    current_user: User = Depends(require_client()),
):
    """Get all applications for a specific specialization within an order"""
    try:
        application_service = OrderApplicationService()
        applications = await application_service.get_applications_by_specialization(order_id, specialization_index)
        return APIResponse(success=True, data=applications)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/eligibility/order/{order_id}", response_model=APIResponse)
async def check_application_eligibility(
    order_id: uuid.UUID = Path(...),
    vacancy_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(require_freelancer()),
):
    """Check if the current freelancer can apply for an order or specific specialization"""
    try:
        freelancer_service = FreelancerService()
        application_service = OrderApplicationService()
        freelancer = await freelancer_service.get_freelancer_by_user_id(current_user.user_id)
        eligibility = await application_service.validate_application_eligibility(
            freelancer.freelancer_id, order_id, vacancy_id
        )
        return APIResponse(success=True, data=eligibility)
    except Exception as e:
        return APIResponse(success=False, error=str(e))
