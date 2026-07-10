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
            .options(selectinload(Order.items), selectinload(Order.payments))
            .order_by(Order.created_at.desc())
        )
        if email:
            # Join with Account to filter by email
            query = (
                select(Order)
                .options(selectinload(Order.items), selectinload(Order.payments))
                .join(Account, Order.account_id == Account.id)
                .where(Account.email == email)
                .order_by(Order.created_at.desc())
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_number(self, order_number: str) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .where(Order.order_number == order_number)
        )
        return result.scalars().first()

    async def save(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.flush()
        return order
