from typing import List, Optional

import uuid

from ..exceptions import BadRequestException, NotFoundException
from ..models.order import OrderStatus
from ..repositories.client import ClientRepository
from ..repositories.company import CompanyRepository
from ..repositories.order import OrderRepository
from ..repositories.order_application import OrderApplicationRepository
from ..repositories.user import UserRepository
from ..schemas.order import (
    OrderAdminResponse,
    OrderCreate,
    OrderRequestHelp,
    OrderResponse,
    OrderSpecialization,
    OrderStatusUpdate,
    OrderUpdate,
)
from ..utils.serialization import safe_model_dump


class OrderService:
    def __init__(
        self,
        order_repo: Optional[OrderRepository] = None,
        client_repo: Optional[ClientRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        user_repo: Optional[UserRepository] = None,
        application_repo: Optional[OrderApplicationRepository] = None,
    ) -> None:
        self.order_repo = order_repo or OrderRepository()
        self.client_repo = client_repo or ClientRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.user_repo = user_repo or UserRepository()
        self.application_repo = application_repo or OrderApplicationRepository()

    async def create_order(self, user_id: uuid.UUID, order_data: OrderCreate) -> OrderResponse:
        await self._ensure_user_profile(user_id, order_data.name, order_data.surname)
        client = await self._ensure_client_profile(user_id)

        company = await self._get_or_create_company(
            client_id=client.client_id,
            company_name=order_data.company_name,
            company_position=order_data.company_position,
        )

        order_payload = safe_model_dump(
            order_data,
            exclude_fields={"name", "surname", "company_name", "company_position"},
        )
        order_payload["company_id"] = str(company.company_id)

        # Initialize specializations with proper structure if they exist
        if order_payload.get("order_specializations"):
            for spec in order_payload["order_specializations"]:
                if isinstance(spec, dict):
                    # Ensure each specialization has required fields for vacancy management
                    if "vacancy_id" not in spec:
                        spec["vacancy_id"] = str(uuid.uuid4())
                    if "is_occupied" not in spec:
                        spec["is_occupied"] = False
                    if "occupied_by_freelancer_id" not in spec:
                        spec["occupied_by_freelancer_id"] = None

        order = await self.order_repo.create(order_payload)
        await self.company_repo.add_order(company.company_id, order.order_id)

        return await self.get_order_response(order)

    async def request_order_help(self, user_id: uuid.UUID, _: OrderRequestHelp) -> OrderResponse:
        await self._ensure_user_profile(user_id)
        client = await self._ensure_client_profile(user_id)

        help_company_id = uuid.uuid4()
        help_company_name = f"Help Request Company {str(help_company_id)}"

        help_company = await self.company_repo.create(
            {
                "client_id": str(client.client_id),
                "owner_ids": [str(client.client_id)],
                "company_name": help_company_name,
                "company_orders": [],
            },
            entity_id=help_company_id,
        )

        await self.client_repo.add_company(client.client_id, help_company.company_id)

        order = await self.order_repo.create(
            {
                "company_id": str(help_company.company_id),
                "order_description": "Help request from client",
            }
        )

        await self.company_repo.add_order(help_company.company_id, order.order_id)
        return await self.get_order_response(order)

    async def get_order(self, order_id: uuid.UUID) -> OrderResponse:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException("Order not found")
        return await self.get_order_response(order)

    async def get_approved_orders(self, skip: int = 0, limit: int = 100) -> List[OrderResponse]:
        orders = await self.order_repo.get_approved_orders(skip, limit)
        return [await self.get_order_response(order) for order in orders]

    async def get_pending_orders(self, skip: int = 0, limit: int = 100) -> List[OrderResponse]:
        orders = await self.order_repo.get_pending_orders(skip, limit)
        return [await self.get_order_response(order) for order in orders]

    async def get_pending_orders_for_admin(self, skip: int = 0, limit: int = 100) -> List[OrderAdminResponse]:
        orders = await self.order_repo.get_pending_orders(skip, limit)
        return [await self.get_order_admin_response(order) for order in orders]

    async def get_orders_by_company(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrderResponse]:
        orders = await self.order_repo.get_by_company_id(company_id, skip, limit)
        return [await self.get_order_response(order) for order in orders]

    async def update_order(self, order_id: uuid.UUID, order_update: OrderUpdate) -> OrderResponse:
        payload = safe_model_dump(order_update, exclude_unset=True)

        # Special handling for order_specializations to preserve vacancy_ids
        if "order_specializations" in payload:
            existing_order = await self.order_repo.get_by_id(order_id)
            if existing_order and existing_order.order_specializations:
                # Create a mapping of existing vacancy_ids by index
                existing_vacancy_ids = {}
                for idx, spec in enumerate(existing_order.order_specializations):
                    if isinstance(spec, dict) and "vacancy_id" in spec:
                        existing_vacancy_ids[idx] = spec["vacancy_id"]

                # Ensure new specializations preserve existing vacancy_ids
                for idx, spec in enumerate(payload["order_specializations"]):
                    if isinstance(spec, dict):
                        if idx in existing_vacancy_ids:
                            # Preserve existing vacancy_id
                            spec["vacancy_id"] = existing_vacancy_ids[idx]
                        elif "vacancy_id" not in spec:
                            # Generate new vacancy_id only if not provided and no existing one
                            spec["vacancy_id"] = str(uuid.uuid4())
                        # Ensure occupation fields are present
                        if "is_occupied" not in spec:
                            spec["is_occupied"] = False
                        if "occupied_by_freelancer_id" not in spec:
                            spec["occupied_by_freelancer_id"] = None

        order = await self.order_repo.update(order_id, payload)
        if not order:
            raise NotFoundException("Order not found")
        return await self.get_order_response(order)

    async def complete_order(self, order_id: uuid.UUID, order_update: OrderUpdate) -> OrderResponse:
        payload = safe_model_dump(order_update, exclude_unset=True)

        payload["order_status"] = OrderStatus.APPROVED.value
        order = await self.order_repo.update(order_id, payload)
        if not order:
            raise NotFoundException("Order not found")
        return await self.get_order_response(order)

    async def update_order_status(
        self,
        order_id: uuid.UUID,
        status_update: OrderStatusUpdate,
    ) -> OrderResponse:
        order = await self.order_repo.update_status(
            order_id,
            status_update.order_status,
            status_update.order_complete_status,
        )
        if not order:
            raise NotFoundException("Order not found")
        return await self.get_order_response(order)

    async def get_order_response(self, order) -> OrderResponse:
        order_specializations = self._deserialize_specializations(order.order_specializations)
        order_colleagues = await self.application_repo.get_accepted_freelancers_by_order(order.order_id)

        return OrderResponse(
            order_id=order.order_id,
            company_id=order.company_id,
            order_description=order.order_description,
            order_status=order.order_status,
            order_complete_status=order.order_complete_status,
            order_title=order.order_title,
            order_colleagues=order_colleagues,
            chat_link=order.chat_link,
            contracts=order.contracts,
            order_specializations=order_specializations,
            order_condition=order.order_condition,
            requirements=order.requirements,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def get_order_admin_response(self, order) -> OrderAdminResponse:
        order_specializations = self._deserialize_specializations(order.order_specializations)
        company = await self.company_repo.get_by_id(order.company_id)
        if not company:
            raise NotFoundException("Company not found for order")

        order_colleagues = await self.application_repo.get_accepted_freelancers_by_order(order.order_id)

        return OrderAdminResponse(
            order_id=order.order_id,
            company_id=order.company_id,
            client_id=company.client_id,
            order_description=order.order_description,
            order_status=order.order_status,
            order_complete_status=order.order_complete_status,
            order_title=order.order_title,
            order_colleagues=order_colleagues,
            chat_link=order.chat_link,
            contracts=order.contracts,
            order_specializations=order_specializations,
            order_condition=order.order_condition,
            requirements=order.requirements,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def get_orders_by_client_user_id(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrderResponse]:
        client = await self.client_repo.get_by_user_id(user_id)
        if not client:
            return []

        companies = await self.company_repo.get_by_client_id(client.client_id)
        orders: List[OrderResponse] = []
        for company in companies:
            company_orders = await self.order_repo.get_by_company_id(company.company_id, skip, limit)
            for order in company_orders:
                orders.append(await self.get_order_response(order))
        return orders

    async def get_order_with_client_id(self, order_id: uuid.UUID) -> OrderAdminResponse:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException("Order not found")
        return await self.get_order_admin_response(order)

    async def _ensure_user_profile(
        self,
        user_id: uuid.UUID,
        name: Optional[str] = None,
        surname: Optional[str] = None,
    ) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        update_payload = {}
        if name is not None and name != user.name:
            update_payload["name"] = name
        if surname is not None and surname != user.surname:
            update_payload["surname"] = surname

        if update_payload:
            await self.user_repo.update(user_id, update_payload)

    async def _ensure_client_profile(self, user_id: uuid.UUID):
        client = await self.client_repo.get_by_user_id(user_id)
        if client:
            return client

        client = await self.client_repo.create(
            {
                "user_id": str(user_id),
                "company_ids": [],
            }
        )
        await self.user_repo.add_role(user_id, "client")
        return client

    async def _get_or_create_company(
        self,
        client_id: uuid.UUID,
        company_name: Optional[str],
        company_position: Optional[str],
    ):
        normalized_name = self.company_repo.normalize_name(company_name)

        if normalized_name:
            existing = await self.company_repo.get_by_normalized_name(normalized_name)
            if existing:
                if client_id not in existing.owner_ids:
                    await self.company_repo.add_owner(existing.company_id, client_id)
                await self.client_repo.add_company(client_id, existing.company_id)
                return await self.company_repo.get_by_id(existing.company_id)

        company_payload = {
            "client_id": str(client_id),
            "company_name": company_name,
            "client_position": company_position,
            "company_orders": [],
            "owner_ids": [str(client_id)],
        }

        company = await self.company_repo.create(company_payload)
        await self.client_repo.add_company(client_id, company.company_id)
        return company

    def _serialize_specializations(
        self,
        specializations: Optional[List[OrderSpecialization]],
    ) -> Optional[List[dict]]:
        if not specializations:
            return None
        return [spec.model_dump() for spec in specializations]

    def _deserialize_specializations(
        self,
        specializations: Optional[List[dict]],
    ) -> Optional[List[OrderSpecialization]]:
        if not specializations:
            return None
        try:
            deserialized_specs = []
            for spec in specializations:
                # Handle UUID field conversions from string to UUID if needed
                spec_copy = spec.copy()
                if "vacancy_id" in spec_copy and isinstance(spec_copy["vacancy_id"], str):
                    spec_copy["vacancy_id"] = uuid.UUID(spec_copy["vacancy_id"])
                elif "vacancy_id" not in spec_copy or spec_copy["vacancy_id"] is None:
                    # Generate vacancy_id if missing (for backward compatibility with existing data)
                    spec_copy["vacancy_id"] = uuid.uuid4()
                if "occupied_by_freelancer_id" in spec_copy and spec_copy["occupied_by_freelancer_id"] is not None and isinstance(spec_copy["occupied_by_freelancer_id"], str):
                    spec_copy["occupied_by_freelancer_id"] = uuid.UUID(spec_copy["occupied_by_freelancer_id"])
                deserialized_specs.append(OrderSpecialization(**spec_copy))
            return deserialized_specs
        except Exception as exc:  # pragma: no cover - defensive
            # Add more detailed error information for debugging
            raise BadRequestException(f"Invalid order specializations format: {str(exc)}") from exc
