"""Test Configuration and Fixtures for FamCore Backend."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Enforce testing environment before importing app
os.environ["APP_ENV"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_famcore.db"

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
async def initialize_test_database():
    """Create test database tables before tests and tear down after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    if os.path.exists("./test_famcore.db"):
        try:
            os.remove("./test_famcore.db")
        except OSError:
            pass


@pytest.fixture
async def client():
    """Async HTTP test client bound to the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
