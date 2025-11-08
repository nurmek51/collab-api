from typing import List, Optional

import uuid

from ..exceptions import NotFoundException
from ..repositories.notification import NotificationRepository
from ..models.notification import NotificationStatus
from ..schemas.notification import NotificationResponse, NotificationUpdate


class NotificationService:
    def __init__(self, notification_repo: Optional[NotificationRepository] = None):
        self.notification_repo = notification_repo or NotificationRepository()

    async def get_admin_notifications(
        self, 
        status: Optional[NotificationStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[NotificationResponse]:
        """Get admin notifications with optional status filter"""
        notifications = await self.notification_repo.get_admin_notifications(status, skip, limit)
        return [
            NotificationResponse(
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
            for notification in notifications
        ]

    async def get_notification(self, notification_id: uuid.UUID) -> NotificationResponse:
        """Get a specific notification"""
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification:
            raise NotFoundException("Notification not found")

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

    async def update_notification(
        self, 
        notification_id: uuid.UUID, 
        update_data: NotificationUpdate
    ) -> NotificationResponse:
        """Update a notification (mark as read/resolved, add admin notes)"""
        update_dict = {}
        
        if update_data.status is not None:
            update_dict["status"] = update_data.status.value
        
        if update_data.admin_notes is not None:
            update_dict["admin_notes"] = update_data.admin_notes

        notification = await self.notification_repo.update(notification_id, update_dict)
        if not notification:
            raise NotFoundException("Notification not found")

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

    async def mark_as_read(self, notification_id: uuid.UUID) -> NotificationResponse:
        """Mark notification as read"""
        notification = await self.notification_repo.mark_as_read(notification_id)
        if not notification:
            raise NotFoundException("Notification not found")

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

    async def mark_as_resolved(
        self, 
        notification_id: uuid.UUID, 
        admin_notes: Optional[str] = None
    ) -> NotificationResponse:
        """Mark notification as resolved with optional admin notes"""
        notification = await self.notification_repo.mark_as_resolved(notification_id, admin_notes)
        if not notification:
            raise NotFoundException("Notification not found")

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