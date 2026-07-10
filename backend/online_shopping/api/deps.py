from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from minio import Minio
from online_shopping.database import async_session
from online_shopping.storage import get_minio_client
from online_shopping.api.auth.jwt import decode_access_token
from online_shopping.models.account import Account
from typing import AsyncGenerator

security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


def get_minio() -> Minio:
    return get_minio_client()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Account:
    """Validate JWT and return the authenticated user. Raises 401 if invalid or missing."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide a Bearer token.",
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    email: str | None = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject.",
        )

    result = await db.execute(
        select(Account)
        .options(selectinload(Account.addresses))
        .where(Account.email == email)
    )
    account = result.scalars().first()
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found.",
        )

    return account


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Account | None:
    """Like get_current_user but returns None instead of raising 401 for unauthenticated requests."""
    if credentials is None:
        return None

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None

    email: str | None = payload.get("sub")
    if email is None:
        return None

    result = await db.execute(
        select(Account)
        .options(selectinload(Account.addresses))
        .where(Account.email == email)
    )
    return result.scalars().first()


# ── Role-based authorization dependencies ─────────────────────────


def _require_role(*allowed_roles: str):
    """Factory: create a dependency that requires one of the given roles."""

    async def role_check(
        current_user: Account = Depends(get_current_user),
    ) -> Account:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {allowed_roles}.",
            )
        return current_user

    return role_check


# Convenience dependencies
require_customer = _require_role("customer", "manager", "admin")
require_manager = _require_role("manager", "admin")
require_admin = _require_role("admin")
