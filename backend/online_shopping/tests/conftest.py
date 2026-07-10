"""Pytest fixtures for online_shopping tests."""

import pytest
from fastapi.testclient import TestClient
from online_shopping.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI TestClient for the application."""
    app = create_app()
    return TestClient(app)
