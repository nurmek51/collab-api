from __future__ import annotations

import uuid
from typing import List, Optional

from ..exceptions import BadRequestException

from .base import FirestoreRepository
from ..models.company import Company


class CompanyRepository(FirestoreRepository[Company]):
    collection_name = "companies"
    id_field = "company_id"

    def __init__(self):
        super().__init__(Company.from_firestore)

    @staticmethod
    def normalize_name(company_name: Optional[str]) -> Optional[str]:
        if not company_name:
            return None
        return company_name.strip().lower()

    async def create(self, payload: dict, entity_id: Optional[uuid.UUID] = None) -> Company:
        normalized = self.normalize_name(payload.get("company_name"))
        if normalized:
            existing = await self.get_by_normalized_name(normalized)
            if existing:
                raise BadRequestException("Company with this name already exists")
            payload["normalized_company_name"] = normalized

        owner_ids = payload.get("owner_ids") or []
        owner_ids = [str(owner_id) for owner_id in owner_ids if owner_id]  # Filter out None/empty values
        client_id = payload.get("client_id")
        if client_id:
            client_id_str = str(client_id)
            if client_id_str not in owner_ids:
                owner_ids.append(client_id_str)
        payload["owner_ids"] = owner_ids

        return await super().create(payload, entity_id=entity_id)

    async def update(self, entity_id: uuid.UUID, payload: dict) -> Optional[Company]:
        if "company_name" in payload:
            normalized = self.normalize_name(payload.get("company_name"))
            if normalized:
                existing = await self.get_by_normalized_name(normalized)
                if existing and existing.company_id != entity_id:
                    raise BadRequestException("Company with this name already exists")
            payload["normalized_company_name"] = normalized

        if "owner_ids" in payload:
            unique_owner_ids: List[str] = []
            for owner_id in payload["owner_ids"]:
                if owner_id:  # Only add non-empty values
                    owner_id_str = str(owner_id)
                    if owner_id_str not in unique_owner_ids:
                        unique_owner_ids.append(owner_id_str)
            existing = await self.get_by_id(entity_id)
            if existing:
                primary_owner = str(existing.client_id)
                if primary_owner not in unique_owner_ids:
                    unique_owner_ids.append(primary_owner)
            payload["owner_ids"] = unique_owner_ids

        return await super().update(entity_id, payload)

    async def get_by_client_id(self, client_id: uuid.UUID) -> List[Company]:
        all_companies = await self.query()
        results: List[Company] = []
        for company in all_companies:
            if client_id in company.owner_ids or company.client_id == client_id:
                results.append(company)
        return results

    async def get_by_normalized_name(self, normalized_name: str) -> Optional[Company]:
        candidates = await self.query(filters=[("normalized_company_name", "==", normalized_name)], limit=1)
        if candidates:
            return candidates[0]
        # fallback for legacy records without normalized field
        all_companies = await self.query()
        for company in all_companies:
            if self.normalize_name(company.company_name) == normalized_name:
                return company
        return None

    async def add_owner(self, company_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[Company]:
        company = await self.get_by_id(company_id)
        if not company:
            return None
        if owner_id in company.owner_ids:
            return company
        updated_owner_ids = [str(oid) for oid in {*company.owner_ids, owner_id}]
        return await self.update(company_id, {"owner_ids": updated_owner_ids})

    async def add_order(self, company_id: uuid.UUID, order_id: uuid.UUID) -> Company:
        company = await self.get_by_id(company_id)
        orders = list({*company.company_orders, order_id}) if company else [order_id]
        payload = {"company_orders": [str(oid) for oid in orders]}
        updated = await self.update(company_id, payload)
        if updated:
            return updated
        # If company did not previously exist in cache, fetch again after update
        return await self.get_by_id(company_id)
