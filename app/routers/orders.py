import uuid

from fastapi import APIRouter, Depends, Path, Query

from ..deps.auth import get_current_user, require_client, require_freelancer
from ..models.user import User
from ..schemas.common import APIResponse, PaginatedResponse
from ..schemas.order import OrderCreate, OrderUpdate
from ..services.order import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/create", response_model=APIResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
):
    try:
        order_service = OrderService()
        order = await order_service.create_order(current_user.user_id, order_data)
        return APIResponse(success=True, data=order)
    except Exception as e:
        return APIResponse(success=False, error=str(e))



@router.get("/my", response_model=APIResponse)
async def get_my_orders(
    current_user: User = Depends(require_client()),
):
    """Get all orders created by the current client"""
    try:
        order_service = OrderService()
        orders = await order_service.get_orders_by_client_user_id(current_user.user_id)
        return APIResponse(success=True, data=orders)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/", response_model=APIResponse)
async def get_approved_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_freelancer()),
):
    try:
        order_service = OrderService()
        skip = (page - 1) * size
        orders = await order_service.get_approved_orders(skip, size)
        
        paginated_response = PaginatedResponse(
            items=orders,
            total=len(orders),
            page=page,
            size=size,
            pages=(len(orders) + size - 1) // size
        )
        return APIResponse(success=True, data=paginated_response)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{order_id}", response_model=APIResponse)
async def get_order(
    order_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
):
    try:
        order_service = OrderService()
        order = await order_service.get_order_with_client_id(order_id)
        return APIResponse(success=True, data=order)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.put("/{order_id}", response_model=APIResponse)
async def update_order(
    order_id: uuid.UUID = Path(...),
    order_update: OrderUpdate = ...,
    current_user: User = Depends(require_client()),
):
    try:
        order_service = OrderService()
        updated_order = await order_service.update_order(order_id, order_update)
        return APIResponse(success=True, data=updated_order)
    except Exception as e:
        return APIResponse(success=False, error=str(e))
