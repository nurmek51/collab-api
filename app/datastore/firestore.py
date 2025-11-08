from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # pragma: no cover - firebase optional at runtime
    from firebase_admin import firestore as admin_firestore
except Exception:  # pragma: no cover - firebase optional at runtime
    admin_firestore = None

from ..config.firebase import get_firestore_client

FilterClause = Tuple[str, str, Any]
OrderClause = Tuple[str, str]


@dataclass
class QueryOptions:
    filters: Iterable[FilterClause] = ()
    limit: Optional[int] = None
    offset: int = 0
    order_by: Optional[OrderClause] = None


class InMemoryStore:
    def __init__(self) -> None:
        self._collections: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            docs = self._collections.get(collection, {})
            data = docs.get(doc_id)
            return None if data is None else data.copy()

    async def create_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        async with self._lock:
            docs = self._collections.setdefault(collection, {})
            docs[doc_id] = data.copy()
            return docs[doc_id].copy()

    async def set_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.create_document(collection, doc_id, data)

    async def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self._lock:
            docs = self._collections.setdefault(collection, {})
            if doc_id not in docs:
                return None
            docs[doc_id].update(data)
            return docs[doc_id].copy()

    async def delete_document(self, collection: str, doc_id: str) -> None:
        async with self._lock:
            docs = self._collections.get(collection)
            if docs and doc_id in docs:
                del docs[doc_id]

    async def query(self, collection: str, options: QueryOptions) -> List[Dict[str, Any]]:
        async with self._lock:
            docs = list(self._collections.get(collection, {}).items())

        def _matches(data: Dict[str, Any]) -> bool:
            for field, op, value in options.filters:
                current = data.get(field)
                if op == "==" and current != value:
                    return False
                if op == "in":
                    if not isinstance(value, list):
                        raise ValueError("Value for 'in' operator must be a list")
                    if current not in value:
                        return False
            return True

        filtered = [(doc_id, data) for doc_id, data in docs if _matches(data)]

        if options.order_by:
            field, direction = options.order_by
            reverse = direction.lower() == "desc"
            filtered.sort(key=lambda item: item[1].get(field), reverse=reverse)

        if options.offset:
            filtered = filtered[options.offset :]

        if options.limit:
            filtered = filtered[: options.limit]

        return [data.copy() for _, data in filtered]

    async def reset(self) -> None:
        async with self._lock:
            self._collections.clear()


class FirestoreStore:
    def __init__(
        self,
        client=None,
        memory_store: Optional[InMemoryStore] = None,
    ) -> None:
        if client is None and memory_store is not None:
            self._client = None
            self._memory = memory_store
        else:
            self._client = client if client is not None else get_firestore_client()
            self._memory = None
            if self._client is None:
                self._memory = memory_store or InMemoryStore()

    async def _run_in_thread(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        if self._memory:
            return await self._memory.get_document(collection, doc_id)

        def _get():
            doc = self._client.collection(collection).document(doc_id).get()
            if not doc.exists:
                return None
            return doc.to_dict()

        return await self._run_in_thread(_get)

    async def create_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if self._memory:
            return await self._memory.create_document(collection, doc_id, data)

        def _create():
            self._client.collection(collection).document(doc_id).set(data)
            return data

        return await self._run_in_thread(_create)

    async def set_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if self._memory:
            return await self._memory.set_document(collection, doc_id, data)

        def _set():
            self._client.collection(collection).document(doc_id).set(data)
            return data

        return await self._run_in_thread(_set)

    async def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self._memory:
            return await self._memory.update_document(collection, doc_id, data)

        def _update():
            doc_ref = self._client.collection(collection).document(doc_id)
            snapshot = doc_ref.get()
            if not snapshot.exists:
                return None
            doc_ref.update(data)
            new_snapshot = doc_ref.get()
            return new_snapshot.to_dict()

        return await self._run_in_thread(_update)

    async def delete_document(self, collection: str, doc_id: str) -> None:
        if self._memory:
            await self._memory.delete_document(collection, doc_id)
            return

        def _delete():
            self._client.collection(collection).document(doc_id).delete()

        await self._run_in_thread(_delete)

    async def query(self, collection: str, options: QueryOptions) -> List[Dict[str, Any]]:
        if self._memory:
            return await self._memory.query(collection, options)

        def _query():
            query = self._client.collection(collection)
            for field, op, value in options.filters:
                query = query.where(field, op, value)
            if options.order_by:
                field, direction = options.order_by
                if admin_firestore is None:
                    query = query.order_by(field)
                else:
                    direction_map = {
                        "asc": admin_firestore.Query.ASCENDING,
                        "desc": admin_firestore.Query.DESCENDING,
                    }
                    query = query.order_by(
                        field,
                        direction=direction_map.get(
                            direction.lower(),
                            admin_firestore.Query.ASCENDING,
                        ),
                    )
            if options.limit:
                query = query.limit(options.limit)
            docs = list(query.stream())
            results = [doc.to_dict() for doc in docs]
            if options.offset:
                results = results[options.offset :]
            return results

        return await self._run_in_thread(_query)

    async def reset(self) -> None:
        if self._memory:
            await self._memory.reset()

    async def healthcheck(self) -> bool:
        if self._memory:
            return True

        def _ping():
            collections = list(self._client.collections())
            # touching the iterator is enough to confirm connectivity
            return len(collections) >= 0

        return await self._run_in_thread(_ping)

    @property
    def using_memory(self) -> bool:
        return self._memory is not None


_MEMORY_STORE = InMemoryStore()
_GLOBAL_STORE: Optional[FirestoreStore] = None


def get_firestore_store() -> FirestoreStore:
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        # Try to get real Firebase client first
        client = get_firestore_client()
        if client is not None:
            print("🔥 Using REAL Firebase Firestore client")
            _GLOBAL_STORE = FirestoreStore(client=client)
        else:
            print("💾 Using IN-MEMORY Firestore store (Firebase not available)")
            _GLOBAL_STORE = FirestoreStore(memory_store=_MEMORY_STORE)
    return _GLOBAL_STORE


async def reset_firestore_store() -> None:
    store = get_firestore_store()
    await store.reset()


async def firestore_healthcheck() -> bool:
    store = get_firestore_store()
    return await store.healthcheck()


async def ensure_timestamps(payload: Dict[str, Any], created: bool = False) -> Dict[str, Any]:
    now = datetime.utcnow()
    data = payload.copy()
    if created and "created_at" not in data:
        data["created_at"] = now
    data["updated_at"] = now
    return data
