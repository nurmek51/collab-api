from typing import List, Optional

import uuid

from ..exceptions import BadRequestException, ConflictException, NotFoundException
from ..models.order_application import ApplicationStatus
from ..repositories.freelancer import FreelancerRepository
from ..repositories.order import OrderRepository
from ..repositories.order_application import OrderApplicationRepository
from ..schemas.order_application import (
    OrderApplicationCreate,
    OrderApplicationResponse,
    OrderApplicationUpdate,
)
from ..utils.serialization import prepare_model_data_for_db, safe_model_dump


class OrderApplicationService:
    def __init__(
        self,
        application_repo: Optional[OrderApplicationRepository] = None,
        order_repo: Optional[OrderRepository] = None,
        freelancer_repo: Optional[FreelancerRepository] = None,
    ) -> None:
        self.application_repo = application_repo or OrderApplicationRepository()
        self.order_repo = order_repo or OrderRepository()
        self.freelancer_repo = freelancer_repo or FreelancerRepository()

    async def create_application(self, freelancer_id: uuid.UUID, application_data: OrderApplicationCreate) -> OrderApplicationResponse:
        freelancer = await self.freelancer_repo.get_by_id(freelancer_id)
        if not freelancer:
            raise NotFoundException("Freelancer not found")

        if freelancer.status.value != "approved":
            raise BadRequestException("Freelancer profile must be approved to apply for orders")

        order = await self.order_repo.get_by_id(application_data.order_id)
        if not order:
            raise NotFoundException("Order not found")

        if order.order_status.value != "approved":
            raise BadRequestException("Cannot apply to unapproved orders")

        # Handle specialization-specific application logic
        specialization_index = None
        specialization_name = None
        
        if application_data.vacancy_id:
            # Check specific specialization
            if order.order_specializations:
                for idx, spec in enumerate(order.order_specializations):
                    if isinstance(spec, dict) and spec.get("vacancy_id") == str(application_data.vacancy_id):
                        specialization_index = idx
                        specialization_name = spec.get("specialization")
                        break
                    elif hasattr(spec, 'vacancy_id') and spec.vacancy_id == application_data.vacancy_id:
                        specialization_index = idx
                        specialization_name = spec.specialization
                        break
                
                if specialization_index is None:
                    raise BadRequestException("Invalid vacancy ID")
                
                # Check if specialization is already occupied
                if await self.application_repo.is_specialization_occupied(application_data.order_id, specialization_index):
                    raise ConflictException("This specialization is already occupied by another freelancer")
                
                # Check if freelancer already has ANY application for this order (prevents multiple applications per order)
                existing_application = await self.application_repo.get_existing_application(
                    application_data.order_id, freelancer_id
                )
                if existing_application:
                    raise ConflictException("You have already applied for this order")
        else:
            # Check for general application (no specific specialization)
            existing_application = await self.application_repo.get_existing_application(
                application_data.order_id, freelancer_id
            )
            if existing_application:
                raise ConflictException("Application already exists for this order")

        application_dict = prepare_model_data_for_db(application_data)
        application_dict["freelancer_id"] = freelancer_id
        application_dict["company_id"] = order.company_id
        application_dict["specialization_index"] = specialization_index
        application_dict["specialization_name"] = specialization_name

        application = await self.application_repo.create(application_dict)
        return await self.get_application_response(application)

    async def get_application(self, application_id: uuid.UUID) -> OrderApplicationResponse:
        application = await self.application_repo.get_by_id(application_id)
        if not application:
            raise NotFoundException("Application not found")
        return await self.get_application_response(application)

    async def get_applications_by_order(self, order_id: uuid.UUID) -> List[OrderApplicationResponse]:
        applications = await self.application_repo.get_by_order_id(order_id)
        return [await self.get_application_response(a) for a in applications]

    async def get_applications_by_freelancer(self, freelancer_id: uuid.UUID) -> List[OrderApplicationResponse]:
        applications = await self.application_repo.get_by_freelancer_id(freelancer_id)
        return [await self.get_application_response(a) for a in applications]

    async def get_applications_by_specialization(self, order_id: uuid.UUID, specialization_index: int) -> List[OrderApplicationResponse]:
        """Get all applications for a specific specialization"""
        applications = await self.application_repo.get_applications_for_specialization(order_id, specialization_index)
        return [await self.get_application_response(a) for a in applications]

    async def update_application_status(self, application_id: uuid.UUID, status_update: OrderApplicationUpdate) -> OrderApplicationResponse:
        application = await self.application_repo.get_by_id(application_id)
        if not application:
            raise NotFoundException("Application not found")

        # If accepting an application for a specific specialization, mark it as occupied
        if status_update.status == ApplicationStatus.ACCEPTED and application.specialization_index is not None:
            await self._mark_specialization_as_occupied(application)
        
        # If rejecting an application that was previously accepted, mark specialization as available
        elif status_update.status == ApplicationStatus.REJECTED and application.status == ApplicationStatus.ACCEPTED and application.specialization_index is not None:
            await self._mark_specialization_as_available(application)

        updated_application = await self.application_repo.update_status(application_id, status_update.status)
        if not updated_application:
            raise NotFoundException("Application not found")
        return await self.get_application_response(updated_application)

    async def get_application_response(self, application) -> OrderApplicationResponse:
        # If application has specialization_index, find the vacancy_id from the order
        vacancy_id = None
        if application.specialization_index is not None:
            order = await self.order_repo.get_by_id(application.order_id)
            if order and order.order_specializations and application.specialization_index < len(order.order_specializations):
                spec = order.order_specializations[application.specialization_index]
                if isinstance(spec, dict):
                    vacancy_id = spec.get("vacancy_id")
                elif hasattr(spec, 'vacancy_id'):
                    vacancy_id = spec.vacancy_id

        return OrderApplicationResponse(
            id=application.id,
            order_id=application.order_id,
            freelancer_id=application.freelancer_id,
            company_id=application.company_id,
            status=application.status,
            specialization_index=application.specialization_index,
            specialization_name=application.specialization_name,
            vacancy_id=uuid.UUID(vacancy_id) if vacancy_id else None,
            created_at=application.created_at,
            updated_at=application.updated_at
        )

    async def get_available_specializations(self, order_id: uuid.UUID) -> List[dict]:
        """Get available (non-occupied) specializations for an order"""
        order = await self.order_repo.get_by_id(order_id)
        if not order or not order.order_specializations:
            return []

        occupied_indices = await self.application_repo.get_occupied_specializations(order_id)
        
        available_specializations = []
        for idx, spec in enumerate(order.order_specializations):
            if idx not in occupied_indices:
                if isinstance(spec, dict):
                    spec_dict = spec.copy()
                    spec_dict["index"] = idx
                    available_specializations.append(spec_dict)
                else:
                    # Handle Pydantic model
                    spec_dict = spec.model_dump() if hasattr(spec, 'model_dump') else spec.dict()
                    spec_dict["index"] = idx
                    available_specializations.append(spec_dict)
        
        return available_specializations

    async def _mark_specialization_as_occupied(self, application) -> None:
        """Mark a specialization as occupied in the order"""
        order = await self.order_repo.get_by_id(application.order_id)
        if not order or not order.order_specializations or application.specialization_index >= len(order.order_specializations):
            return

        # Update the specialization to mark it as occupied
        specialization = order.order_specializations[application.specialization_index]
        if isinstance(specialization, dict):
            specialization["is_occupied"] = True
            specialization["occupied_by_freelancer_id"] = str(application.freelancer_id)
        else:
            # Handle Pydantic model
            specialization.is_occupied = True
            specialization.occupied_by_freelancer_id = application.freelancer_id

        # Update the order in the database
        await self.order_repo.update(application.order_id, {"order_specializations": order.order_specializations})

    async def _mark_specialization_as_available(self, application) -> None:
        """Mark a specialization as available in the order"""
        order = await self.order_repo.get_by_id(application.order_id)
        if not order or not order.order_specializations or application.specialization_index >= len(order.order_specializations):
            return

        # Update the specialization to mark it as available
        specialization = order.order_specializations[application.specialization_index]
        if isinstance(specialization, dict):
            specialization["is_occupied"] = False
            specialization["occupied_by_freelancer_id"] = None
        else:
            # Handle Pydantic model
            specialization.is_occupied = False
        # Update the order in the database
        await self.order_repo.update(application.order_id, {"order_specializations": order.order_specializations})

    async def validate_application_eligibility(self, freelancer_id: uuid.UUID, order_id: uuid.UUID, vacancy_id: Optional[uuid.UUID] = None) -> dict:
        """Validate if a freelancer can apply for an order or specific specialization"""
        freelancer = await self.freelancer_repo.get_by_id(freelancer_id)
        if not freelancer:
            return {"eligible": False, "reason": "Freelancer not found"}

        if freelancer.status.value != "approved":
            return {"eligible": False, "reason": "Freelancer profile must be approved to apply for orders"}

        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return {"eligible": False, "reason": "Order not found"}

        if order.order_status.value != "approved":
            return {"eligible": False, "reason": "Cannot apply to unapproved orders"}

        if vacancy_id:
            # Check specific specialization
            if order.order_specializations:
                specialization_index = None
                for idx, spec in enumerate(order.order_specializations):
                    if isinstance(spec, dict) and spec.get("vacancy_id") == str(vacancy_id):
                        specialization_index = idx
                        break
                    elif hasattr(spec, 'vacancy_id') and spec.vacancy_id == vacancy_id:
                        specialization_index = idx
                        break
                
                if specialization_index is None:
                    return {"eligible": False, "reason": "Invalid vacancy ID"}
                
                # Check if specialization is already occupied
                if await self.application_repo.is_specialization_occupied(order_id, specialization_index):
                    return {"eligible": False, "reason": "This specialization is already occupied by another freelancer"}
                
                # Check if freelancer already has ANY application for this order (prevents multiple applications per order)
                existing_application = await self.application_repo.get_existing_application(order_id, freelancer_id)
                if existing_application:
                    return {"eligible": False, "reason": "You have already applied for this order"}
        else:
            # Check general application (no specific specialization)
            existing_application = await self.application_repo.get_existing_application(order_id, freelancer_id)
            if existing_application:
                return {"eligible": False, "reason": "Application already exists for this order"}

        return {"eligible": True, "reason": "Eligible to apply"}
