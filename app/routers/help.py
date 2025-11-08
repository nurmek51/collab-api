from fastapi import APIRouter, Depends

from ..deps.auth import get_current_user
from ..models.user import User
from ..schemas.common import APIResponse
from ..schemas.order import AdminHelpRequest
from ..schemas.notification import NotificationResponse
from ..services.admin_help import AdminHelpService

router = APIRouter(tags=["Admin Help"])


@router.post("/request-help", response_model=APIResponse)
async def request_admin_help(
    help_request: AdminHelpRequest,
    current_user: User = Depends(get_current_user),
):
    """Universal endpoint for requesting admin help with any context"""
    try:
        help_service = AdminHelpService()
        notification = await help_service.create_help_request(current_user.user_id, help_request)
        return APIResponse(success=True, data=notification)
    except Exception as e:
        return APIResponse(success=False, error=str(e))
