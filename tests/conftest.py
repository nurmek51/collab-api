import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.datastore.firestore import reset_firestore_store
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _reset_store():
    await reset_firestore_store()
    yield
    await reset_firestore_store()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
