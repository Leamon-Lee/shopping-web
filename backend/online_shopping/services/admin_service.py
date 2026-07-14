"""Admin service — platform-wide aggregated data for admin dashboard."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, func, case, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.product import Product
from online_shopping.models.category import ProductCategory
from online_shopping.models.order import Order, OrderItem
from online_shopping.models.account import Account
from online_shopping.models.shop import Shop, ShopProduct


class AdminService:
    """Provides platform-wide aggregated data for admin operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def dashboard(self) -> dict:
        """Platform-level dashboard stats."""
        product_count = (await self.db.execute(select(func.count(Product.id)))).scalar() or 0
        category_count = (await self.db.execute(select(func.count(ProductCategory.id)))).scalar() or 0
        order_count = (await self.db.execute(select(func.count(Order.id)))).scalar() or 0

        # User counts by role
        customer_count = (
            await self.db.execute(
                select(func.count(Account.id)).where(Account.role == "customer")
            )
        ).scalar() or 0
        manager_count = (
            await self.db.execute(
                select(func.count(Account.id)).where(Account.role == "manager")
            )
        ).scalar() or 0
        admin_count = (
            await self.db.execute(
                select(func.count(Account.id)).where(Account.role == "admin")
            )
        ).scalar() or 0

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
                "categories": category_count,
                "orders": order_count,
                "customers": customer_count,
                "managers": manager_count,
                "admins": admin_count,
                "total_users": customer_count + manager_count + admin_count,
            },
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

    async def list_users(self) -> list[dict]:
        """List all platform users."""
        result = await self.db.execute(
            select(Account)
            .options(selectinload(Account.addresses))
            .order_by(Account.created_at.desc())
            .limit(100)
        )
        users = list(result.scalars().all())
        return [
            {
                "id": str(u.id),
                "user_name": u.user_name,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
                "status": u.status,
                "addresses_count": len(u.addresses),
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]

    async def list_products(self) -> list[dict]:
        """List all platform products."""
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category), selectinload(Product.variants))
            .order_by(Product.created_at.desc())
            .limit(100)
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
                "images": len(p.images),
            }
            for p in products
        ]

    async def list_orders(self) -> list[dict]:
        """List all platform orders."""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .order_by(Order.created_at.desc())
            .limit(100)
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

    async def category_preferences(
        self, start_date: date, end_date: date
    ) -> list[dict]:
        """Order count by product category for a given date range."""
        base = (
            select(
                ProductCategory.name.label("category_name"),
                func.count(func.distinct(Order.id)).label("order_count"),
                func.coalesce(
                    func.sum(OrderItem.price * OrderItem.quantity), 0
                ).label("sales_amount"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .join(ProductCategory, ProductCategory.id == Product.category_id)
            .where(Order.order_date >= start_date)
            .where(Order.order_date <= end_date)
            .group_by(ProductCategory.name)
            .order_by(func.count(func.distinct(Order.id)).desc())
        )
        result = await self.db.execute(base)
        return [
            {
                "category_name": row.category_name,
                "order_count": row.order_count,
                "sales_amount": float(row.sales_amount),
            }
            for row in result
        ]

    async def daily_rankings(self, query_date: date) -> dict:
        """Shop and product order rankings for a specific date."""
        # Shop rankings
        shop_q = (
            select(
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
            .where(cast(Order.order_date, Date) == query_date)
            .group_by(Shop.id, Shop.name)
            .order_by(func.count(func.distinct(Order.id)).desc())
            .limit(15)
        )
        shop_rows = (await self.db.execute(shop_q)).all()

        # Product rankings
        prod_q = (
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                func.count(func.distinct(Order.id)).label("order_count"),
                func.coalesce(
                    func.sum(OrderItem.price * OrderItem.quantity), 0
                ).label("sales_amount"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(cast(Order.order_date, Date) == query_date)
            .group_by(Product.id, Product.name)
            .order_by(func.count(func.distinct(Order.id)).desc())
            .limit(15)
        )
        prod_rows = (await self.db.execute(prod_q)).all()

        return {
            "date": query_date.isoformat(),
            "shop_rankings": [
                {
                    "shop_id": str(r.shop_id),
                    "shop_name": r.shop_name,
                    "order_count": r.order_count,
                    "sales_amount": float(r.sales_amount),
                }
                for r in shop_rows
            ],
            "product_rankings": [
                {
                    "product_id": str(r.product_id),
                    "product_name": r.product_name,
                    "order_count": r.order_count,
                    "sales_amount": float(r.sales_amount),
                }
                for r in prod_rows
            ],
        }
