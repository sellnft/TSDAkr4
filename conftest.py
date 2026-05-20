import pytest
from typing import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from main11_2 import app, clear_db

@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest.fixture(scope="function")
def clean_db():
    clear_db()
    yield
    clear_db()

@pytest.fixture(scope="session")
def faker_seed():
    return 42