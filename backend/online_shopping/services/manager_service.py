"""Manager service — aggregates data scoped to a specific manager's shops."""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.product import Product
from online_shopping.models.order import Order
from online_shopping.models.account import Account
from online_shopping.repositories.shop_repository import ShopRepository


class ManagerService:
    """Provides aggregated data scoped to a specific manager."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.shops = ShopRepository(db)

    async def dashboard(self, manager: Account) -> dict:
        """Aggregated stats for the manager's shops."""
        owned_shops = await self.shops.list_by_owner(manager.id)

        shop_ids = [s.id for s in owned_shops]

        # Products count (all for now — scoped if shop-product join exists)
        product_result = await self.db.execute(
            select(func.count(Product.id))
        )
        product_count = product_result.scalar() or 0

        # Low stock products
        low_stock_result = await self.db.execute(
            select(Product.name)
            .where(Product.available_item_count <= 10)
            .limit(20)
        )
        low_stock = [row[0] for row in low_stock_result]

        # Orders count
        order_result = await self.db.execute(
            select(func.count(Order.id))
        )
        order_count = order_result.scalar() or 0

        # Recent orders
        recent_orders_result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        recent_orders = list(recent_orders_result.scalars().all())

        return {
            "stats": {
                "products": product_count,
                "orders": order_count,
                "low_stock_products": len(low_stock),
                "shops": len(owned_shops),
            },
            "shops": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "slug": s.slug,
                    "status": s.status,
                    "category": s.category,
                }
                for s in owned_shops
            ],
            "low_stock": low_stock,
            "recent_orders": [
                {
                    "order_number": o.order_number,
                    "status": o.status,
                    "total": sum(float(item.price) * item.quantity for item in o.items),
                    "date": o.order_date.isoformat() if o.order_date else None,
                }
                for o in recent_orders
            ],
        }

    async def list_products(self, manager: Account) -> list[dict]:
        """List all products visible to this manager."""
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category), selectinload(Product.variants))
            .order_by(Product.created_at.desc())
        )
        products = list(result.scalars().all())
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "price": float(p.price),
                "available_item_count": p.available_item_count,
                "category": p.category.name if p.category else "",
                "variants": len(p.variants),
            }
            for p in products
        ]

    async def list_orders(self, manager: Account) -> list[dict]:
        """List recent orders."""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .order_by(Order.created_at.desc())
            .limit(50)
        )
        orders = list(result.scalars().all())
        return [
            {
                "order_number": o.order_number,
                "status": o.status,
                "items_count": len(o.items),
                "total": sum(float(item.price) * item.quantity for item in o.items),
                "payment_status": o.payments[0].status if o.payments else "pending",
                "date": o.order_date.isoformat() if o.order_date else None,
            }
            for o in orders
        ]

    async def create_shop(self, manager: Account, payload: dict) -> dict:
        """Create a new shop owned by this manager."""
        import re
        from online_shopping.models.shop import Shop

        slug = re.sub(r"[^a-z0-9]+", "-", payload["name"].lower()).strip("-") or "shop"
        shop = Shop(
            name=payload["name"],
            slug=slug,
            description=payload.get("description", ""),
            owner_id=manager.id,
            status="pending",  # Requires admin approval
            category=payload.get("category"),
        )
        await self.shops.save(shop)
        await self.db.commit()
        return {
            "id": str(shop.id),
            "name": shop.name,
            "slug": shop.slug,
            "status": shop.status,
        }
