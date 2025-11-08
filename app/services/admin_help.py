from typing import Optional

import uuid

from ..exceptions import NotFoundException
from ..repositories.user import UserRepository
from ..repositories.client import ClientRepository
from ..repositories.company import CompanyRepository
from ..repositories.order import OrderRepository
from ..repositories.notification import NotificationRepository
from ..models.notification import NotificationType, NotificationStatus
from ..schemas.order import AdminHelpRequest
from ..schemas.notification import NotificationResponse


class AdminHelpService:
    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        client_repo: Optional[ClientRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        order_repo: Optional[OrderRepository] = None,
        notification_repo: Optional[NotificationRepository] = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.client_repo = client_repo or ClientRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.order_repo = order_repo or OrderRepository()
        self.notification_repo = notification_repo or NotificationRepository()

    async def create_help_request(self, user_id: uuid.UUID, help_request: AdminHelpRequest) -> NotificationResponse:
        """Create an admin help request notification and raw order"""
        try:
            # Validate user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise NotFoundException("User not found")

            # Get or create client profile for the user
            client = await self.client_repo.get_by_user_id(user_id)
            if not client:
                # Create client profile
                client_data = {
                    "user_id": str(user_id),
                    "company_ids": []
                }
                client = await self.client_repo.create(client_data)

            # Create a help company for the client
            help_company_id = uuid.uuid4()
            help_company_name = f"Help Request Company {str(help_company_id)}"

            help_company = await self.company_repo.create({
                "client_id": str(client.client_id),
                "owner_ids": [str(client.client_id)],
                "company_name": help_company_name,
                "company_orders": [],
            }, entity_id=help_company_id)

            await self.client_repo.add_company(client.client_id, help_company.company_id)

            # Create a raw order for the help request
            # Create user display name for notifications
            user_display_name = f"{user.name or 'Unknown'} {user.surname or ''}".strip()
            if user_display_name == "Unknown":
                user_display_name = f"User {user.phone_number or str(user_id)[:8]}"

            order_data = {
                "order_description": f"Help request from {user_display_name}",
                "order_title": "Admin Help Request",
                "company_id": str(help_company.company_id)
            }

            order = await self.order_repo.create(order_data)

            # Add order to company
            await self.company_repo.add_order(help_company.company_id, order.order_id)

            # Create admin notification
            notification_data = {
                "type": NotificationType.HELP_REQUEST.value,
                "status": NotificationStatus.PENDING.value,
                "title": "New Help Request",
                "message": f"{user_display_name} requested admin help",
                "user_id": str(user_id),
                "client_id": str(client.client_id),
                "order_id": str(order.order_id),
                "reason": help_request.reason,
            }

            notification = await self.notification_repo.create(notification_data)

            return NotificationResponse(
                notification_id=notification.notification_id,
                type=notification.type,
                status=notification.status,
                title=notification.title,
                message=notification.message,
                user_id=notification.user_id,
                client_id=notification.client_id,
                order_id=notification.order_id,
                reason=notification.reason,
                admin_notes=notification.admin_notes,
                created_at=notification.created_at,
                updated_at=notification.updated_at,
            )
        except Exception as e:
            raise e
