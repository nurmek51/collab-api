from __future__ import annotations

import uuid
from typing import List, Optional

from ..repositories.company import CompanyRepository
from ..repositories.client import ClientRepository
from ..repositories.order import OrderRepository
from ..repositories.order_application import OrderApplicationRepository
from ..schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from ..exceptions import NotFoundException, BadRequestException
from ..utils.serialization import safe_model_dump


class CompanyService:
    def __init__(
        self,
        company_repo: Optional[CompanyRepository] = None,
        client_repo: Optional[ClientRepository] = None,
        order_repo: Optional[OrderRepository] = None,
        application_repo: Optional[OrderApplicationRepository] = None,
    ):
        self.company_repo = company_repo or CompanyRepository()
        self.client_repo = client_repo or ClientRepository()
        self.order_repo = order_repo or OrderRepository()
        self.application_repo = application_repo or OrderApplicationRepository()

    async def create_company(self, client_id: uuid.UUID, company_data: CompanyCreate) -> CompanyResponse:
        client = await self.client_repo.get_by_id(client_id)
        if not client:
            raise NotFoundException("Client not found")

        payload = safe_model_dump(company_data, exclude_unset=True)
        normalized_name = self.company_repo.normalize_name(payload.get("company_name"))
        if normalized_name:
            existing = await self.company_repo.get_by_normalized_name(normalized_name)
            if existing:
                raise BadRequestException("Company with this name already exists")

        payload.update({
            "client_id": str(client_id),
            "company_orders": [],
            "owner_ids": [str(client_id)],
        })

        company = await self.company_repo.create(payload)
        await self.client_repo.add_company(client_id, company.company_id)
        refreshed = await self.company_repo.get_by_id(company.company_id)
        return await self._build_response(refreshed)

    async def get_company(self, company_id: uuid.UUID) -> CompanyResponse:
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise NotFoundException("Company not found")
        return await self._build_response(company)

    async def get_companies_by_client(self, client_id: uuid.UUID) -> List[CompanyResponse]:
        companies = await self.company_repo.get_by_client_id(client_id)
        return [await self._build_response(company) for company in companies]

    async def get_all_companies(self) -> List[CompanyResponse]:
        companies = await self.company_repo.query()
        return [await self._build_response(company) for company in companies]

    async def update_company(self, company_id: uuid.UUID, company_update: CompanyUpdate) -> CompanyResponse:
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise NotFoundException("Company not found")

        update_payload = safe_model_dump(company_update, exclude_unset=True)
        if update_payload:
            await self.company_repo.update(company_id, update_payload)

        refreshed = await self.company_repo.get_by_id(company_id)
        return await self._build_response(refreshed)

    async def _build_response(self, company) -> CompanyResponse:
        if not company:
            raise NotFoundException("Company not found")

        orders_data = []
        for order_id in company.company_orders or []:
            order = await self.order_repo.get_by_id(order_id)
            if not order:
                continue
            order_colleagues = await self.application_repo.get_accepted_freelancers_by_order(order_id)
            orders_data.append({
                "order_id": order.order_id,
                "company_id": order.company_id,
                "order_description": order.order_description,
                "order_status": order.order_status.value,
                "order_complete_status": order.order_complete_status.value,
                "order_title": order.order_title,
                "order_colleagues": order_colleagues,
                "chat_link": order.chat_link,
                "contracts": order.contracts,
                "order_specializations": order.order_specializations,
                "created_at": order.created_at,
                "updated_at": order.updated_at,
            })

        return CompanyResponse(
            company_id=company.company_id,
            client_id=company.client_id,
            owner_ids=company.owner_ids,
            company_industry=company.company_industry,
            client_position=company.client_position,
            company_name=company.company_name,
            company_size=company.company_size,
            company_logo=company.company_logo,
            company_description=company.company_description,
            company_orders=company.company_orders or [],
            orders=orders_data,
            created_at=company.created_at,
            updated_at=company.updated_at,
        )
