from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.account import Account
from online_shopping.models.order import Order


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_orders(self, email: str | None = None) -> list[Order]:
        query = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments), selectinload(Order.shipments))
            .order_by(Order.created_at.desc())
        )
        if email:
            query = (
                select(Order)
                .options(selectinload(Order.items), selectinload(Order.payments), selectinload(Order.shipments))
                .join(Account, Order.account_id == Account.id)
                .where(Account.email == email)
                .order_by(Order.created_at.desc())
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_number(self, order_number: str) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments), selectinload(Order.shipments))
            .where(Order.order_number == order_number)
        )
        return result.scalars().first()

    async def get_by_number_and_token(self, order_number: str, access_token: str) -> Order | None:
        """Guest-secure lookup: requires both order_number and access_token."""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments), selectinload(Order.shipments))
            .where(Order.order_number == order_number, Order.order_access_token == access_token)
        )
        return result.scalars().first()

    async def save(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.flush()
        return order

    async def list_by_shop_owner(
        self, owner_id, shop_ids: list, limit: int = 50
    ) -> list[Order]:
        """List orders that contain items from any of the given shop_ids."""
        if not shop_ids:
            return []
        from online_shopping.models.order import OrderItem
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments), selectinload(Order.shipments))
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(OrderItem.shop_id.in_(shop_ids))
            .distinct()
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
