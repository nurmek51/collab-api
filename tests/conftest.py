import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock

# We MUST patch get_firestore_client during import to ensure tests don't touch production DB
with patch("app.config.firebase.get_firestore_client", return_value=None):
    from app.datastore.firestore import reset_firestore_store, get_firestore_store, FirestoreStore, InMemoryStore
    import app.datastore.firestore as fs_module
    from app.main import app


@pytest.fixture(autouse=True)
def mock_twilio():
    with patch("app.services.auth.TwilioService") as mock:
        instance = mock.return_value
        instance.send_otp = AsyncMock(return_value=True)
        instance.verify_otp = AsyncMock(return_value=True)
        yield instance


@pytest_asyncio.fixture(autouse=True)
async def _reset_store():
    # Force InMemoryStore if somehow real store leaked
    current_store = get_firestore_store()
    if not current_store.using_memory:
        fs_module._GLOBAL_STORE = FirestoreStore(memory_store=InMemoryStore())
        print("FORCED using InMemoryStore for test safety")
    
    await reset_firestore_store()
    yield
    await reset_firestore_store()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
