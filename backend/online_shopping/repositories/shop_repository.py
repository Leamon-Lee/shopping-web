"""Shop repository — database access for Shop CRUD and ownership queries."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.shop import Shop


class ShopRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Shop]:
        result = await self.db.execute(
            select(Shop)
            .options(selectinload(Shop.owner))
            .where(Shop.owner_id == owner_id)
            .order_by(Shop.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Shop]:
        result = await self.db.execute(
            select(Shop)
            .options(selectinload(Shop.owner))
            .order_by(Shop.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, shop_id: uuid.UUID) -> Shop | None:
        result = await self.db.execute(
            select(Shop)
            .options(selectinload(Shop.owner))
            .where(Shop.id == shop_id)
        )
        return result.scalars().first()

    async def save(self, shop: Shop) -> Shop:
        self.db.add(shop)
        await self.db.flush()
        return shop

    async def update_status(self, shop: Shop, status: str) -> Shop:
        shop.status = status
        await self.db.flush()
        return shop

    async def delete(self, shop: Shop) -> None:
        await self.db.delete(shop)
        await self.db.flush()
