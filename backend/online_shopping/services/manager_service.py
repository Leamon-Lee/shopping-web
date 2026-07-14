"""Manager service — aggregates data scoped to a specific manager's shops."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.product import Product
from online_shopping.models.order import Order, OrderItem
from online_shopping.models.account import Account
from online_shopping.models.shop import ShopProduct, Shop
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

    async def shop_order_analytics(
        self, manager: Account, days: int = 7, shop_id: str | None = None
    ) -> list[dict]:
        """Daily order count and sales per shop for the last N days."""
        shop_ids = await self._shop_ids(manager)
        if not shop_ids:
            return []

        if shop_id:
            from uuid import UUID as _UUID
            shop_ids = [s for s in shop_ids if s == _UUID(shop_id)]
            if not shop_ids:
                return []

        cutoff = datetime.utcnow() - timedelta(days=days)

        base = (
            select(
                cast(Order.order_date, Date).label("date"),
                Shop.id.label("shop_id"),
                Shop.name.label("shop_name"),
                func.count(func.distinct(Order.id)).label("order_count"),
                func.coalesce(
                    func.sum(OrderItem.price * OrderItem.quantity), 0
                ).label("sales_amount"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(ShopProduct, ShopProduct.product_id == OrderItem.product_id)
            .join(Shop, Shop.id == ShopProduct.shop_id)
            .where(Order.order_date >= cutoff)
            .where(ShopProduct.shop_id.in_(shop_ids))
            .group_by(cast(Order.order_date, Date), Shop.id, Shop.name)
            .order_by("date")
        )

        result = await self.db.execute(base)
        return [
            {
                "date": str(row.date),
                "shop_id": str(row.shop_id),
                "shop_name": row.shop_name,
                "order_count": row.order_count,
                "sales_amount": float(row.sales_amount),
            }
            for row in result
        ]

    async def dashboard_analytics(
        self, manager: Account, category_id: str | None = None
    ) -> dict:
        """Return analytics cards: top shop, top product, predictions."""
        shop_ids = await self._shop_ids(manager)
        if not shop_ids:
            return {
                "top_shop": None,
                "top_product": None,
                "predicted_shop": None,
                "predicted_product": None,
                "categories": [],
            }

        cutoff_7d = datetime.utcnow() - timedelta(days=7)

        def _base_select(*extra_cols):
            cols = list(extra_cols) + [
                func.count(func.distinct(Order.id)).label("order_count"),
                func.coalesce(
                    func.sum(OrderItem.price * OrderItem.quantity), 0
                ).label("sales_amount"),
            ]
            q = (
                select(*cols)
                .select_from(Order)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .join(ShopProduct, ShopProduct.product_id == OrderItem.product_id)
                .join(Shop, Shop.id == ShopProduct.shop_id)
                .where(Order.order_date >= cutoff_7d)
                .where(ShopProduct.shop_id.in_(shop_ids))
            )
            if category_id:
                q = q.where(
                    OrderItem.product_id.in_(
                        select(Product.id).where(Product.category_id == category_id)
                    )
                )
            return q

        # Top shop
        top_shop_q = (
            _base_select(Shop.id.label("shop_id"), Shop.name.label("shop_name"))
            .group_by(Shop.id, Shop.name)
            .order_by(func.count(func.distinct(Order.id)).desc())
            .limit(1)
        )
        shop_row = (await self.db.execute(top_shop_q)).first()

        # Top product
        top_product_q = (
            _base_select(
                Product.id.label("product_id"), Product.name.label("product_name")
            )
            .join(Product, Product.id == OrderItem.product_id)
            .group_by(Product.id, Product.name)
            .order_by(func.count(func.distinct(Order.id)).desc())
            .limit(1)
        )
        prod_row = (await self.db.execute(top_product_q)).first()

        # Predictions: same month/day range last year
        today = datetime.utcnow().date()
        hist_start = today.replace(year=today.year - 1)
        hist_end = (today + timedelta(days=6)).replace(year=today.year - 1)

        def _prediction_base(*extra_cols):
            cols = list(extra_cols) + [
                func.count(func.distinct(Order.id)).label("order_count"),
            ]
            q = (
                select(*cols)
                .select_from(Order)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .join(ShopProduct, ShopProduct.product_id == OrderItem.product_id)
                .join(Shop, Shop.id == ShopProduct.shop_id)
                .where(Order.order_date >= hist_start)
                .where(Order.order_date <= hist_end)
                .where(ShopProduct.shop_id.in_(shop_ids))
            )
            if category_id:
                q = q.where(
                    OrderItem.product_id.in_(
                        select(Product.id).where(Product.category_id == category_id)
                    )
                )
            return q

        pred_shop_q = (
            _prediction_base(Shop.id.label("shop_id"), Shop.name.label("shop_name"))
            .group_by(Shop.id, Shop.name)
            .order_by(func.count(func.distinct(Order.id)).desc())
            .limit(1)
        )
        pred_shop_row = (await self.db.execute(pred_shop_q)).first()

        pred_prod_q = (
            _prediction_base(
                Product.id.label("product_id"), Product.name.label("product_name")
            )
            .join(Product, Product.id == OrderItem.product_id)
            .group_by(Product.id, Product.name)
            .order_by(func.count(func.distinct(Order.id)).desc())
            .limit(1)
        )
        pred_prod_row = (await self.db.execute(pred_prod_q)).first()

        # Categories for filter dropdown
        from online_shopping.models.category import ProductCategory

        cat_result = await self.db.execute(
            select(ProductCategory.id, ProductCategory.name)
            .select_from(ProductCategory)
            .join(Product, Product.category_id == ProductCategory.id)
            .join(ShopProduct, ShopProduct.product_id == Product.id)
            .where(ShopProduct.shop_id.in_(shop_ids))
            .distinct()
            .order_by(ProductCategory.name)
        )
        categories = [
            {"id": str(c[0]), "name": c[1]} for c in cat_result
        ]

        def _format_shop(row):
            if row is None:
                return None
            return {
                "shop_id": str(row.shop_id),
                "shop_name": row.shop_name,
                "order_count": row.order_count,
                "sales_amount": float(row.sales_amount),
            }

        def _format_product(row):
            if row is None:
                return None
            return {
                "product_id": str(row.product_id),
                "product_name": row.product_name,
                "order_count": row.order_count,
            }

        def _format_pred_shop(row):
            if row is None:
                return None
            return {
                "shop_id": str(row.shop_id),
                "shop_name": row.shop_name,
                "predicted_daily_orders": max(1, int(row.order_count / 7 + 0.5)),
            }

        def _format_pred_product(row):
            if row is None:
                return None
            return {
                "product_id": str(row.product_id),
                "product_name": row.product_name,
                "predicted_daily_orders": max(1, int(row.order_count / 7 + 0.5)),
            }

        return {
            "top_shop": _format_shop(shop_row),
            "top_product": _format_product(prod_row),
            "predicted_shop": _format_pred_shop(pred_shop_row),
            "predicted_product": _format_pred_product(pred_prod_row),
            "categories": categories,
        }

    async def list_categories(self, manager: Account) -> list[tuple]:
        """Return distinct categories for products in manager's shops."""
        shop_ids = await self._shop_ids(manager)
        if not shop_ids:
            return []

        from online_shopping.models.category import ProductCategory

        result = await self.db.execute(
            select(ProductCategory.id, ProductCategory.name)
            .select_from(ProductCategory)
            .join(Product, Product.category_id == ProductCategory.id)
            .join(ShopProduct, ShopProduct.product_id == Product.id)
            .where(ShopProduct.shop_id.in_(shop_ids))
            .distinct()
            .order_by(ProductCategory.name)
        )
        return [(r[0], r[1]) for r in result]
