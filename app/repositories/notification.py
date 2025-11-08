import uuid
from typing import List, Optional

from .base import FirestoreRepository
from ..models.notification import Notification, NotificationStatus, NotificationType


class NotificationRepository(FirestoreRepository[Notification]):
    collection_name = "notifications"
    id_field = "notification_id"

    def __init__(self):
        super().__init__(Notification.from_firestore)

    async def get_admin_notifications(
        self, 
        status: Optional[NotificationStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Notification]:
        """Get notifications for admin with optional status filter"""
        filters = []
        if status:
            filters.append(("status", "==", status.value))
        
        return await self.query(
            filters=filters,
            limit=limit,
            offset=skip,
            order_by=("created_at", "desc"),
        )

    async def get_by_user_id(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Notification]:
        """Get notifications for a specific user"""
        return await self.query(
            filters=[("user_id", "==", str(user_id))],
            limit=limit,
            offset=skip,
            order_by=("created_at", "desc"),
        )

    async def get_by_order_id(self, order_id: uuid.UUID) -> List[Notification]:
        """Get notifications related to a specific order"""
        return await self.query(
            filters=[("order_id", "==", str(order_id))],
            order_by=("created_at", "desc"),
        )

    async def mark_as_read(self, notification_id: uuid.UUID) -> Optional[Notification]:
        """Mark notification as read"""
        return await self.update(notification_id, {"status": NotificationStatus.READ.value})

    async def mark_as_resolved(self, notification_id: uuid.UUID, admin_notes: Optional[str] = None) -> Optional[Notification]:
        """Mark notification as resolved with optional admin notes"""
        update_data = {"status": NotificationStatus.RESOLVED.value}
        if admin_notes:
            update_data["admin_notes"] = admin_notes
        return await self.update(notification_id, update_data)

    async def count_pending_by_type(self, notification_type: NotificationType) -> int:
        """Count pending notifications by type"""
        notifications = await self.query(
            filters=[
                ("type", "==", notification_type.value),
                ("status", "==", NotificationStatus.PENDING.value)
            ]
        )
        return len(notifications)