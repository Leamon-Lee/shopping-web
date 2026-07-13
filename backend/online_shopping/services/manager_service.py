"""Manager service — aggregates data scoped to a specific manager's shops."""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.product import Product
from online_shopping.models.order import Order, OrderItem
from online_shopping.models.account import Account
from online_shopping.models.shop import ShopProduct
from online_shopping.repositories.shop_repository import ShopRepository


class ManagerService:
    """Provides aggregated data scoped to a specific manager."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.shops = ShopRepository(db)

    async def _shop_ids(self, manager: Account) -> list:
        owned = await self.shops.list_by_owner(manager.id)
        return [s.id for s in owned]

    async def dashboard(self, manager: Account) -> dict:
        """Aggregated stats for the manager's shops."""
        owned_shops = await self.shops.list_by_owner(manager.id)
        shop_ids = [s.id for s in owned_shops]

        if not shop_ids:
            return {
                "stats": {"products": 0, "orders": 0, "low_stock_products": 0, "shops": 0},
                "shops": [],
                "low_stock": [],
                "recent_orders": [],
            }

        # Product count scoped to manager's shops via shop_products
        product_result = await self.db.execute(
            select(func.count(ShopProduct.product_id))
            .where(ShopProduct.shop_id.in_(shop_ids))
        )
        product_count = product_result.scalar() or 0

        # Low stock products scoped to manager's shops
        low_stock_result = await self.db.execute(
            select(Product.name)
            .select_from(Product)
            .join(ShopProduct, ShopProduct.product_id == Product.id)
            .where(ShopProduct.shop_id.in_(shop_ids))
            .where(Product.available_item_count <= 10)
            .limit(20)
        )
        low_stock = [row[0] for row in low_stock_result]

        # Orders count scoped via order_items -> shop_products
        order_result = await self.db.execute(
            select(func.count())
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(ShopProduct, ShopProduct.product_id == OrderItem.product_id)
            .where(ShopProduct.shop_id.in_(shop_ids))
        )
        order_count = order_result.scalar() or 0

        # Recent orders scoped to manager's shops
        recent_orders_result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(ShopProduct, ShopProduct.product_id == OrderItem.product_id)
            .where(ShopProduct.shop_id.in_(shop_ids))
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
        """List products belonging to this manager's shops."""
        shop_ids = await self._shop_ids(manager)
        if not shop_ids:
            return []

        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category), selectinload(Product.variants))
            .join(ShopProduct, ShopProduct.product_id == Product.id)
            .where(ShopProduct.shop_id.in_(shop_ids))
            .order_by(Product.created_at.desc())
        )
        products = list(set(result.scalars().all()))

        # Fetch product-shop mapping
        product_shops: dict[str, list[str]] = {}
        if products:
            shop_map_result = await self.db.execute(
                select(ShopProduct.product_id, ShopProduct.shop_id)
                .where(ShopProduct.product_id.in_([p.id for p in products]))
            )
            for pid, sid in shop_map_result:
                key = str(pid)
                if key not in product_shops:
                    product_shops[key] = []
                product_shops[key].append(str(sid))

        return [
            {
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "price": float(p.price),
                "available_item_count": p.available_item_count,
                "category": p.category.name if p.category else "",
                "variants": len(p.variants),
                "shop_ids": product_shops.get(str(p.id), []),
            }
            for p in products
        ]

    async def list_orders(self, manager: Account) -> list[dict]:
        """List orders that involve products from this manager's shops."""
        shop_ids = await self._shop_ids(manager)
        if not shop_ids:
            return []

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(ShopProduct, ShopProduct.product_id == OrderItem.product_id)
            .where(ShopProduct.shop_id.in_(shop_ids))
            .order_by(Order.created_at.desc())
            .limit(50)
        )
        orders = list(set(result.scalars().all()))
        orders.sort(key=lambda o: o.created_at or "", reverse=True)
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
