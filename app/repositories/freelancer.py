from typing import List, Optional

import uuid

from .base import FirestoreRepository
from ..models.freelancer import Freelancer, FreelancerStatus


class FreelancerRepository(FirestoreRepository[Freelancer]):
    collection_name = "freelancers"
    id_field = "freelancer_id"

    def __init__(self):
        super().__init__(Freelancer.from_firestore)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Freelancer]:
        freelancers = await self.query(filters=[("user_id", "==", str(user_id))], limit=1)
        return freelancers[0] if freelancers else None

    async def get_by_email(self, email: str) -> Optional[Freelancer]:
        freelancers = await self.query(filters=[("email", "==", email)], limit=1)
        return freelancers[0] if freelancers else None

    async def get_pending_freelancers(self, skip: int = 0, limit: int = 100) -> List[Freelancer]:
        return await self.query(
            filters=[("status", "==", FreelancerStatus.PENDING.value)],
            limit=limit,
            offset=skip,
        )

    async def get_approved_freelancers(self, skip: int = 0, limit: int = 100) -> List[Freelancer]:
        return await self.query(
            filters=[("status", "==", FreelancerStatus.APPROVED.value)],
            limit=limit,
            offset=skip,
        )

    async def count_by_status(self, status: FreelancerStatus) -> int:
        freelancers = await self.query(filters=[("status", "==", status.value)])
        return len(freelancers)

    async def update_status(self, freelancer_id: uuid.UUID, status: FreelancerStatus) -> Optional[Freelancer]:
        return await self.update(freelancer_id, {"status": status.value})
