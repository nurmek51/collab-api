import uuid
from typing import List, Optional

from .base import FirestoreRepository
from ..datastore.firestore import ensure_timestamps
from ..models.order import Order, OrderCompleteStatus, OrderStatus


class OrderRepository(FirestoreRepository[Order]):
    collection_name = "orders"
    id_field = "order_id"

    def __init__(self):
        super().__init__(Order.from_firestore)

    async def get_by_id_with_company(self, order_id: uuid.UUID) -> Optional[Order]:
        # Relationships are resolved in services; return order data only
        return await self.get_by_id(order_id)

    async def get_approved_orders(self, skip: int = 0, limit: int = 100) -> List[Order]:
        return await self.query(
            filters=[("order_status", "==", OrderStatus.APPROVED.value)],
            limit=limit,
            offset=skip,
        )

    async def get_pending_orders(self, skip: int = 0, limit: int = 100) -> List[Order]:
        return await self.query(
            filters=[("order_status", "==", OrderStatus.PENDING.value)],
            limit=limit,
            offset=skip,
        )

    async def get_by_company_id(self, company_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Order]:
        return await self.query(
            filters=[("company_id", "==", str(company_id))],
            limit=limit,
            offset=skip,
        )

    async def count_by_status(self, status: OrderStatus) -> int:
        orders = await self.query(filters=[("order_status", "==", status.value)])
        return len(orders)

    async def update_status(
        self,
        order_id: uuid.UUID,
        order_status: Optional[OrderStatus] = None,
        complete_status: Optional[OrderCompleteStatus] = None,
    ) -> Optional[Order]:
        payload = {}
        if order_status:
            payload["order_status"] = order_status.value
        if complete_status:
            payload["order_complete_status"] = complete_status.value
        if not payload:
            return await self.get_by_id(order_id)
        return await self.update(order_id, payload)

    async def create(self, payload: dict, entity_id: Optional[uuid.UUID] = None) -> Order:
        order_id = entity_id or uuid.uuid4()
        payload = payload.copy()
        payload["order_id"] = str(order_id)
        order = self._factory(payload)
        data = order.to_firestore()
        data = await ensure_timestamps(data, created=True)
        await self._store.set_document(self.collection_name, str(order_id), data)
        return order
