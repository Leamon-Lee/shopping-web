"""Pytest fixtures for online_shopping tests."""

import os

import pytest
from fastapi.testclient import TestClient


def _db_available() -> bool:
    """Check if a PostgreSQL database is reachable."""
    try:
        import asyncpg
        import asyncio

        async def _check():
            conn = await asyncpg.connect(
                os.getenv("DATABASE_URL", "postgresql://shopping_user:shopping_password@localhost:5432/shopping"),
                timeout=3,
            )
            await conn.close()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(_check())
        return True
    except Exception:
        return False


DB_AVAILABLE = _db_available()


@pytest.fixture(scope="session")
def db_available() -> bool:
    """Whether a PostgreSQL database is available for integration tests."""
    return DB_AVAILABLE


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Create a FastAPI TestClient for the application (session-scoped to avoid event-loop issues)."""
    from online_shopping.api.app import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c
