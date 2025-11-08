from __future__ import annotations

import uuid
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, TypeVar

from ..datastore.firestore import (
    FirestoreStore,
    QueryOptions,
    ensure_timestamps,
    get_firestore_store,
)

T = TypeVar("T")


class FirestoreRepository(Generic[T]):
    collection_name: str
    id_field: str

    def __init__(
        self,
        factory: Callable[[Dict[str, Any]], T],
        store: Optional[FirestoreStore] = None,
    ):
        self._factory = factory
        self._store = store or get_firestore_store()

    async def create(self, payload: Dict[str, Any], entity_id: Optional[uuid.UUID] = None) -> T:
        doc_id = str(entity_id or uuid.uuid4())
        payload = payload.copy()
        payload[self.id_field] = doc_id
        payload = await ensure_timestamps(payload, created=True)
        await self._store.set_document(self.collection_name, doc_id, payload)
        return self._factory(payload)

    async def upsert(self, payload: Dict[str, Any], entity_id: uuid.UUID) -> T:
        doc_id = str(entity_id)
        payload = payload.copy()
        payload[self.id_field] = doc_id
        payload = await ensure_timestamps(payload, created=False)
        await self._store.set_document(self.collection_name, doc_id, payload)
        return self._factory(payload)

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        doc_id = str(entity_id)
        document = await self._store.get_document(self.collection_name, doc_id)
        if not document:
            return None
        document.setdefault(self.id_field, doc_id)
        try:
            return self._factory(document)
        except (ValueError, TypeError) as e:
            print(f"WARNING: Invalid document with ID {doc_id}: {e}")
            return None

    async def query(
        self,
        filters: Iterable[tuple[str, str, Any]] = (),
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[tuple[str, str]] = None,
    ) -> List[T]:
        options = QueryOptions(filters=filters, limit=limit, offset=offset, order_by=order_by)
        documents = await self._store.query(self.collection_name, options)
        results: List[T] = []
        for document in documents:
            if self.id_field not in document:
                continue
            try:
                results.append(self._factory(document))
            except (ValueError, TypeError) as e:
                print(f"WARNING: Skipping invalid document {document.get(self.id_field, 'UNKNOWN')}: {e}")
                continue
        return results

    async def update(self, entity_id: uuid.UUID, payload: Dict[str, Any]) -> Optional[T]:
        doc_id = str(entity_id)
        payload = await ensure_timestamps(payload, created=False)
        document = await self._store.update_document(self.collection_name, doc_id, payload)
        if not document:
            return None
        document.setdefault(self.id_field, doc_id)
        return self._factory(document)

    async def delete(self, entity_id: uuid.UUID) -> None:
        doc_id = str(entity_id)
        await self._store.delete_document(self.collection_name, doc_id)
