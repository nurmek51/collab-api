import uuid
from typing import List, Optional

from .base import FirestoreRepository
from ..datastore.firestore import ensure_timestamps
from ..models.order_application import ApplicationStatus, OrderApplication


class OrderApplicationRepository(FirestoreRepository[OrderApplication]):
    collection_name = "order_applications"
    id_field = "id"

    def __init__(self):
        super().__init__(OrderApplication.from_firestore)

    async def create(self, payload: dict, entity_id: Optional[uuid.UUID] = None) -> OrderApplication:
        app_id = entity_id or uuid.uuid4()
        payload = payload.copy()
        payload["id"] = str(app_id)
        payload["status"] = ApplicationStatus.PENDING.value  # Set default status
        application = self._factory(payload)
        data = application.to_firestore()
        data = await ensure_timestamps(data, created=True)
        await self._store.set_document(self.collection_name, str(app_id), data)
        return application

    async def get_by_order_id(self, order_id: uuid.UUID) -> List[OrderApplication]:
        return await self.query(filters=[("order_id", "==", str(order_id))])

    async def get_by_freelancer_id(self, freelancer_id: uuid.UUID) -> List[OrderApplication]:
        return await self.query(filters=[("freelancer_id", "==", str(freelancer_id))])

    async def get_existing_application(self, order_id: uuid.UUID, freelancer_id: uuid.UUID) -> Optional[OrderApplication]:
        applications = await self.query(
            filters=[
                ("order_id", "==", str(order_id)),
                ("freelancer_id", "==", str(freelancer_id)),
            ],
            limit=1,
        )
        return applications[0] if applications else None

    async def get_existing_application_for_specialization(self, order_id: uuid.UUID, freelancer_id: uuid.UUID, specialization_index: int) -> Optional[OrderApplication]:
        """Check if freelancer already applied for this specific specialization"""
        applications = await self.query(
            filters=[
                ("order_id", "==", str(order_id)),
                ("freelancer_id", "==", str(freelancer_id)),
                ("specialization_index", "==", specialization_index),
            ],
            limit=1,
        )
        return applications[0] if applications else None

    async def get_applications_for_specialization(self, order_id: uuid.UUID, specialization_index: int) -> List[OrderApplication]:
        """Get all applications for a specific specialization"""
        return await self.query(
            filters=[
                ("order_id", "==", str(order_id)),
                ("specialization_index", "==", specialization_index),
            ]
        )

    async def get_accepted_freelancers_by_order(self, order_id: uuid.UUID) -> List[uuid.UUID]:
        applications = await self.query(
            filters=[
                ("order_id", "==", str(order_id)),
                ("status", "==", ApplicationStatus.ACCEPTED.value),
            ]
        )
        return [application.freelancer_id for application in applications]

    async def is_specialization_occupied(self, order_id: uuid.UUID, specialization_index: int) -> bool:
        """Check if a specialization is already occupied by an accepted application"""
        accepted_applications = await self.query(
            filters=[
                ("order_id", "==", str(order_id)),
                ("specialization_index", "==", specialization_index),
                ("status", "==", ApplicationStatus.ACCEPTED.value),
            ],
            limit=1,
        )
        return len(accepted_applications) > 0

    async def get_occupied_specializations(self, order_id: uuid.UUID) -> List[int]:
        """Get list of specialization indices that are occupied (have accepted applications)"""
        accepted_applications = await self.query(
            filters=[
                ("order_id", "==", str(order_id)),
                ("status", "==", ApplicationStatus.ACCEPTED.value),
            ]
        )
        return [app.specialization_index for app in accepted_applications if app.specialization_index is not None]

    async def update_status(self, application_id: uuid.UUID, status: ApplicationStatus) -> Optional[OrderApplication]:
        return await self.update(application_id, {"status": status.value})
