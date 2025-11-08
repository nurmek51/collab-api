from __future__ import annotations

import uuid
from typing import List, Optional

from ..repositories.freelancer import FreelancerRepository
from ..repositories.user import UserRepository
from ..schemas.freelancer import (
    FreelancerApproval,
    FreelancerCreate,
    FreelancerResponse,
    FreelancerStatus as SchemaFreelancerStatus,
    FreelancerUpdate,
    Specialization,
)
from ..models.freelancer import FreelancerStatus as ModelFreelancerStatus
from ..exceptions import ConflictException, NotFoundException
from ..utils.serialization import safe_model_dump


class FreelancerService:
    def __init__(
        self,
        freelancer_repo: Optional[FreelancerRepository] = None,
        user_repo: Optional[UserRepository] = None,
    ):
        self.freelancer_repo = freelancer_repo or FreelancerRepository()
        self.user_repo = user_repo or UserRepository()

    async def create_freelancer_profile(
        self,
        user_id: uuid.UUID,
        freelancer_data: FreelancerCreate,
    ) -> FreelancerResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        if await self.freelancer_repo.get_by_user_id(user_id):
            raise ConflictException("Freelancer profile already exists")

        if await self.freelancer_repo.get_by_email(freelancer_data.email):
            raise ConflictException("Email already registered")

        user_update = {
            key: getattr(freelancer_data, key)
            for key in ("name", "surname", "phone_number")
            if getattr(freelancer_data, key) is not None
        }

        payload = safe_model_dump(freelancer_data, exclude_unset=True)
        for key in ("name", "surname", "phone_number"):
            payload.pop(key, None)

        payload.update({
            "user_id": str(user_id),
            "status": ModelFreelancerStatus.PENDING.value,
        })

        freelancer = await self.freelancer_repo.create(payload)

        if user_update:
            await self.user_repo.update(user_id, user_update)

        await self.user_repo.add_role(user_id, "freelancer")

        refreshed = await self.freelancer_repo.get_by_id(freelancer.freelancer_id)
        return await self._build_response(refreshed)

    async def get_freelancer(self, freelancer_id: uuid.UUID) -> FreelancerResponse:
        freelancer = await self.freelancer_repo.get_by_id(freelancer_id)
        if not freelancer:
            raise NotFoundException("Freelancer not found")
        return await self._build_response(freelancer)

    async def get_freelancer_by_user_id(self, user_id: uuid.UUID) -> FreelancerResponse:
        freelancer = await self.freelancer_repo.get_by_user_id(user_id)
        if not freelancer:
            raise NotFoundException("Freelancer profile not found")
        return await self._build_response(freelancer)

    async def get_freelancer_by_id(self, freelancer_id: uuid.UUID) -> FreelancerResponse:
        return await self.get_freelancer(freelancer_id)

    async def update_freelancer(self, freelancer_id: uuid.UUID, freelancer_update: FreelancerUpdate) -> FreelancerResponse:
        freelancer = await self.freelancer_repo.get_by_id(freelancer_id)
        if not freelancer:
            raise NotFoundException("Freelancer not found")

        update_payload = safe_model_dump(freelancer_update, exclude_unset=True)

        user_update = {}
        for field in ("name", "surname", "phone_number"):
            if field in update_payload:
                user_update[field] = update_payload.pop(field)

        if "email" in update_payload:
            existing_email = await self.freelancer_repo.get_by_email(update_payload["email"])
            if existing_email and existing_email.freelancer_id != freelancer_id:
                raise ConflictException("Email already registered")

        if update_payload:
            await self.freelancer_repo.update(freelancer_id, update_payload)

        if user_update:
            await self.user_repo.update(freelancer.user_id, user_update)

        refreshed = await self.freelancer_repo.get_by_id(freelancer_id)
        return await self._build_response(refreshed)

    async def get_pending_freelancers(self, skip: int = 0, limit: int = 100) -> List[FreelancerResponse]:
        freelancers = await self.freelancer_repo.get_pending_freelancers(skip, limit)
        return [await self._build_response(f) for f in freelancers]

    async def get_approved_freelancers(self, skip: int = 0, limit: int = 100) -> List[FreelancerResponse]:
        freelancers = await self.freelancer_repo.get_approved_freelancers(skip, limit)
        return [await self._build_response(f) for f in freelancers]

    async def approve_freelancer(self, freelancer_id: uuid.UUID, approval: FreelancerApproval) -> FreelancerResponse:
        status = ModelFreelancerStatus(approval.status.value)
        updated = await self.freelancer_repo.update_status(freelancer_id, status)
        if not updated:
            raise NotFoundException("Freelancer not found")
        refreshed = await self.freelancer_repo.get_by_id(freelancer_id)
        return await self._build_response(refreshed)

    async def _build_response(self, freelancer) -> FreelancerResponse:
        if not freelancer:
            raise NotFoundException("Freelancer not found")

        user = await self.user_repo.get_by_id(freelancer.user_id)
        if not user:
            raise NotFoundException("User not found")

        specializations = [Specialization(**spec) for spec in freelancer.specializations_with_levels or []]
        status = SchemaFreelancerStatus(freelancer.status.value)

        return FreelancerResponse(
            freelancer_id=freelancer.freelancer_id,
            user_id=freelancer.user_id,
            iin=freelancer.iin,
            city=freelancer.city,
            email=freelancer.email,
            specializations_with_levels=specializations,
            experience_description=freelancer.experience_description or "",
            name=user.name or "",
            surname=user.surname or "",
            phone_number=user.phone_number,
            status=status,
            payment_info=freelancer.payment_info,
            social_links=freelancer.social_links,
            portfolio_links=freelancer.portfolio_links,
            avatar_url=freelancer.avatar_url,
            bio=freelancer.bio,
            created_at=freelancer.created_at,
            updated_at=freelancer.updated_at,
        )

