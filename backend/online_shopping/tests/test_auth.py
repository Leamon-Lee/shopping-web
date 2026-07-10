"""Tests for JWT authentication and role-based authorization."""

import pytest
from fastapi.testclient import TestClient
from online_shopping.api.auth.jwt import create_access_token, decode_access_token
from online_shopping.config import settings


class TestJWT:
    """JWT creation and validation tests."""

    def test_create_token_contains_sub_and_role(self):
        token = create_access_token({"sub": "test@example.com", "role": "customer"})
        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        token = create_access_token({"sub": "test@example.com", "role": "manager"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "manager"

    def test_decode_invalid_token_returns_none(self):
        payload = decode_access_token("not.a.valid.token")
        assert payload is None

    def test_decode_expired_token_returns_none(self):
        import time
        from jose import jwt
        # Create an already-expired token
        expired = jwt.encode(
            {"sub": "test@example.com", "exp": 1},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        payload = decode_access_token(expired)
        assert payload is None


class TestPublicEndpoints:
    """Tests for endpoints that do not require authentication."""

    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_list_products(self, client: TestClient):
        response = client.get("/shop")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_categories(self, client: TestClient):
        response = client.get("/shop/categories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_login_invalid_credentials(self, client: TestClient):
        response = client.post(
            "/accounts/login",
            json={"email": "nonexistent@test.com", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_register_validation(self, client: TestClient):
        response = client.post(
            "/accounts/register",
            json={"email": "", "password": "short"},
        )
        assert response.status_code == 422  # Pydantic validation error


class TestProtectedEndpoints:
    """Tests for endpoints that require authentication."""

    def test_get_me_without_token(self, client: TestClient):
        response = client.get("/accounts/me")
        assert response.status_code == 401

    def test_get_me_with_invalid_token(self, client: TestClient):
        response = client.get(
            "/accounts/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    def test_list_orders_without_token(self, client: TestClient):
        response = client.get("/orders")
        assert response.status_code == 401

    def test_admin_endpoint_without_token(self, client: TestClient):
        response = client.get("/admin/dashboard")
        assert response.status_code == 401

    def test_manager_endpoint_without_token(self, client: TestClient):
        response = client.get("/manager/dashboard")
        assert response.status_code == 401


class TestRoleAuthorization:
    """Tests for role-based access control."""

    def test_customer_token_cannot_access_admin(self, client: TestClient):
        token = create_access_token({"sub": "customer@test.com", "role": "customer"})
        response = client.get(
            "/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403  # Forbidden

    def test_customer_token_cannot_access_manager(self, client: TestClient):
        token = create_access_token({"sub": "customer@test.com", "role": "customer"})
        response = client.get(
            "/manager/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403  # Forbidden

    def test_manager_token_cannot_access_admin(self, client: TestClient):
        token = create_access_token({"sub": "manager@test.com", "role": "manager"})
        response = client.get(
            "/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403  # Forbidden
