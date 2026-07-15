"""Seed historical orders (2025-07 ~ 2025-12) for manager dashboard predictions.

Usage:
    cd backend && python -m scripts.seed_historical_orders

Only run once — handles duplicate order_numbers gracefully.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone, date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.database import async_session
from online_shopping.models.account import Account
from online_shopping.models.order import Order, OrderItem
from online_shopping.models.payment import Payment
from online_shopping.models.product import Product
from online_shopping.models.shop import Shop, ShopProduct

# ── config ─────────────────────────────────────────────────────────────

TOTAL_ORDERS = 600
START_DATE = date(2025, 7, 1)
END_DATE = date(2025, 12, 31)
STATUSES = ["created", "confirmed", "shipped", "completed"]
STATUS_WEIGHTS = [0.25, 0.10, 0.20, 0.45]

# ── helpers ────────────────────────────────────────────────────────────


def random_date(start: date, end: date) -> datetime:
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    hour = random.randint(8, 22)
    minute = random.randint(0, 59)
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=timezone.utc)


def weighted_choice(choices: list[str], weights: list[float]) -> str:
    return random.choices(choices, weights=weights, k=1)[0]


async def seed(limit: int = TOTAL_ORDERS):
    async with async_session() as session:
        s: AsyncSession = session

        # ── fetch existing data ──────────────────────────────────────
        shops_result = await s.execute(
            select(Shop).where(Shop.status == "active")
        )
        shops = list(shops_result.scalars().all())
        if not shops:
            print("No active shops found. Seed skipped.")
            return

        # build shop->products map
        shop_product_map: dict[uuid.UUID, list[Product]] = {}
        for shop in shops:
            sp_result = await s.execute(
                select(Product)
                .join(ShopProduct, ShopProduct.product_id == Product.id)
                .where(ShopProduct.shop_id == shop.id)
            )
            prods = list(sp_result.scalars().all())
            if prods:
                shop_product_map[shop.id] = prods

        if not shop_product_map:
            print("No shops with products. Seed skipped.")
            return

        customers_result = await s.execute(
            select(Account).where(Account.role == "customer")
        )
        customers = list(customers_result.scalars().all())
        if not customers:
            print("No customer accounts. Seed skipped.")
            return

        # ── check existing historical orders ──────────────────────────
        existing = await s.execute(
            select(Order).where(Order.order_date >= datetime(2025, 7, 1, tzinfo=timezone.utc))
        )
        existing_count = len(list(existing.scalars().all()))
        if existing_count > 0:
            print(f"Found {existing_count} existing 2025 orders.  "
                  f"Generating {limit} more on top.")
            # use a different counter prefix to avoid collisions
            counter_start = existing_count + 10_000
        else:
            counter_start = 1

        created = 0
        batch: list[Order] = []

        for i in range(limit):
            shop = random.choice(shops)
            products_in_shop = shop_product_map.get(shop.id)
            if not products_in_shop:
                continue

            customer = random.choice(customers)
            order_date = random_date(START_DATE, END_DATE)
            order_number = f"HIST-{counter_start + i:06d}"

            status = weighted_choice(STATUSES, STATUS_WEIGHTS)

            order = Order(
                account_id=customer.id,
                order_number=order_number,
                status=status,
                order_date=order_date,
                created_at=order_date,
                updated_at=order_date,
            )

            # 1-4 line items
            item_count = random.randint(1, min(4, len(products_in_shop)))
            chosen = random.sample(products_in_shop, item_count)
            total = 0.0
            for product in chosen:
                qty = random.randint(1, 3)
                price = float(product.price)
                total += price * qty
                order.items.append(
                    OrderItem(
                        product_id=product.id,
                        product_name=product.name,
                        quantity=qty,
                        price=price,
                        created_at=order_date,
                    )
                )

            order.payments.append(
                Payment(
                    status="completed" if status in ("shipped", "completed") else "pending",
                    amount=total,
                    currency="CNY",
                    created_at=order_date,
                )
            )

            batch.append(order)
            created += 1

            # flush every 100 to keep memory low
            if len(batch) >= 100:
                s.add_all(batch)
                await s.flush()
                batch.clear()

        if batch:
            s.add_all(batch)
            await s.flush()

        await s.commit()
        print(f"Seeded {created} historical orders (2025-07 ~ 2025-12).")


if __name__ == "__main__":
    asyncio.run(seed())
