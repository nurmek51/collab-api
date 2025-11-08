import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query

from ..deps.auth import require_admin
from ..models.user import User
from ..models.notification import NotificationStatus
from ..schemas.common import APIResponse, PaginatedResponse
from ..schemas.freelancer import FreelancerApproval
from ..schemas.order import OrderStatusUpdate, OrderUpdate
from ..schemas.notification import NotificationResponse, NotificationUpdate
from ..services.freelancer import FreelancerService
from ..services.order import OrderService
from ..services.notification import NotificationService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/notifications", response_model=APIResponse)
async def get_admin_notifications(
    current_user: User = Depends(require_admin()),
):
    """Get admin notifications including pending freelancers, orders, and help requests"""
    try:
        freelancer_service = FreelancerService()
        order_service = OrderService()
        notification_service = NotificationService()

        # Get pending freelancers (limit to 10 for summary)
        pending_freelancers = await freelancer_service.get_pending_freelancers(0, 10)

        # Get pending orders (limit to 10 for summary)
        pending_orders = await order_service.get_pending_orders_for_admin(0, 10)

        # Get help request notifications (limit to 10 for summary)
        help_notifications = await notification_service.get_admin_notifications(
            NotificationStatus.PENDING, 0, 10
        )

        notifications = {
            "pending_freelancers": len(pending_freelancers),
            "pending_orders": len(pending_orders),
            "pending_help_requests": len(help_notifications),
            "recent_freelancers": pending_freelancers,
            "recent_orders": pending_orders,
            "recent_help_requests": help_notifications
        }

        return APIResponse(success=True, data=notifications)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/notifications/summary", response_model=APIResponse)
async def get_admin_notifications_summary(
    current_user: User = Depends(require_admin()),
):
    """Get a summary of pending notifications and orders for admin dashboard"""
    try:
        freelancer_service = FreelancerService()
        order_service = OrderService()
        notification_service = NotificationService()
        
        pending_freelancers = await freelancer_service.get_pending_freelancers(0, 10)
        pending_orders = await order_service.get_pending_orders_for_admin(0, 10)
        pending_notifications = await notification_service.get_admin_notifications(
            NotificationStatus.PENDING, 0, 10
        )
        
        notifications = {
            "pending_freelancers": len(pending_freelancers),
            "pending_orders": len(pending_orders),
            "pending_help_requests": len(pending_notifications),
            "recent_freelancers": pending_freelancers,
            "recent_orders": pending_orders,
            "recent_help_requests": pending_notifications
        }
        
        return APIResponse(success=True, data=notifications)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/help-requests", response_model=APIResponse)
async def get_help_requests(
    status: Optional[NotificationStatus] = Query(None, description="Filter by notification status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin()),
):
    """Get help request notifications with optional status filter"""
    try:
        notification_service = NotificationService()
        skip = (page - 1) * size
        notifications = await notification_service.get_admin_notifications(status, skip, size)

        paginated_response = PaginatedResponse(
            items=notifications,
            total=len(notifications),
            page=page,
            size=size,
            pages=(len(notifications) + size - 1) // size
        )

        return APIResponse(success=True, data=paginated_response)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.put("/help-requests/{notification_id}", response_model=APIResponse)
async def update_help_request(
    notification_id: uuid.UUID = Path(...),
    update_data: NotificationUpdate = ...,
    current_user: User = Depends(require_admin()),
):
    """Update a help request notification (mark as read/resolved, add admin notes)"""
    try:
        notification_service = NotificationService()
        notification = await notification_service.update_notification(notification_id, update_data)
        return APIResponse(success=True, data=notification)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/help-requests/{notification_id}/read", response_model=APIResponse)
async def mark_help_request_as_read(
    notification_id: uuid.UUID = Path(...),
    current_user: User = Depends(require_admin()),
):
    """Mark a help request notification as read"""
    try:
        notification_service = NotificationService()
        notification = await notification_service.mark_as_read(notification_id)
        return APIResponse(success=True, data=notification)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/help-requests/{notification_id}/resolve", response_model=APIResponse)
async def resolve_help_request(
    notification_id: uuid.UUID = Path(...),
    admin_notes: Optional[str] = Query(None, description="Optional admin notes"),
    current_user: User = Depends(require_admin()),
):
    """Mark a help request notification as resolved with optional admin notes"""
    try:
        notification_service = NotificationService()
        notification = await notification_service.mark_as_resolved(notification_id, admin_notes)
        return APIResponse(success=True, data=notification)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/freelancers/pending", response_model=APIResponse)
async def get_pending_freelancers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin()),
):
    try:
        freelancer_service = FreelancerService()
        skip = (page - 1) * size
        freelancers = await freelancer_service.get_pending_freelancers(skip, size)
        
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


@router.put("/freelancers/{freelancer_id}/approve", response_model=APIResponse)
async def approve_freelancer(
    freelancer_id: uuid.UUID = Path(...),
    approval: FreelancerApproval = ...,
    current_user: User = Depends(require_admin()),
):
    try:
        freelancer_service = FreelancerService()
        freelancer = await freelancer_service.approve_freelancer(freelancer_id, approval)
        return APIResponse(success=True, data=freelancer)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/orders/pending", response_model=APIResponse)
async def get_pending_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin()),
):
    try:
        order_service = OrderService()
        skip = (page - 1) * size
        orders = await order_service.get_pending_orders_for_admin(skip, size)
        
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


@router.post("/orders/{order_id}/complete", response_model=APIResponse)
async def complete_order(
    order_id: uuid.UUID = Path(...),
    order_update: OrderUpdate = ...,
    current_user: User = Depends(require_admin()),
):
    try:
        order_service = OrderService()
        order = await order_service.complete_order(order_id, order_update)
        return APIResponse(success=True, data=order)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.put("/orders/{order_id}/status", response_model=APIResponse)
async def update_order_status(
    order_id: uuid.UUID = Path(...),
    status_update: OrderStatusUpdate = ...,
    current_user: User = Depends(require_admin()),
):
    try:
        order_service = OrderService()
        order = await order_service.update_order_status(order_id, status_update)
        return APIResponse(success=True, data=order)
    except Exception as e:
        return APIResponse(success=False, error=str(e))
