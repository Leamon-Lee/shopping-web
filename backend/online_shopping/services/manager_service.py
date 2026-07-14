"""Manager service — all data scoped to the manager's own shops."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.account import Account
from online_shopping.models.order import Order, OrderItem
from online_shopping.models.payment import Payment
from online_shopping.models.product import Product
from online_shopping.models.product_variant import ProductVariant
from online_shopping.models.shipment import Shipment
from online_shopping.models.shop import Shop
from online_shopping.repositories.shop_repository import ShopRepository


class ManagerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.shops = ShopRepository(db)

    async def _get_shop_ids(self, manager_id: uuid.UUID) -> list[uuid.UUID]:
        shops = await self.shops.list_by_owner(manager_id)
        return [s.id for s in shops if s.status == "active"]

    async def _owned_active_shops(self, manager_id: uuid.UUID) -> list[Shop]:
        shops = await self.shops.list_by_owner(manager_id)
        return [s for s in shops if s.status == "active"]

    # ── Dashboard ─────────────────────────────────────────────────

    async def dashboard(self, manager: Account) -> dict:
        shop_ids = await self._get_shop_ids(manager.id)

        # Products count
        if shop_ids:
            prod_result = await self.db.execute(
                text(
                    "SELECT COUNT(*) FROM products p "
                    "JOIN shop_products sp ON sp.product_id = p.id "
                    "WHERE sp.shop_id = ANY(:sids)"
                ),
                {"sids": shop_ids},
            )
            product_count = prod_result.scalar() or 0
        else:
            product_count = 0

        # Orders count
        if shop_ids:
            ord_result = await self.db.execute(
                text(
                    "SELECT COUNT(DISTINCT oi.order_id) FROM order_items oi "
                    "WHERE oi.shop_id = ANY(:sids)"
                ),
                {"sids": shop_ids},
            )
            order_count = ord_result.scalar() or 0
        else:
            order_count = 0

        # Low stock
        if shop_ids:
            low_result = await self.db.execute(
                text(
                    "SELECT p.name FROM products p "
                    "JOIN shop_products sp ON sp.product_id = p.id "
                    "WHERE sp.shop_id = ANY(:sids) AND p.available_item_count <= 10 "
                    "LIMIT 10"
                ),
                {"sids": shop_ids},
            )
            low_stock = [row[0] for row in low_result]
        else:
            low_stock = []

        owned_shops = await self.shops.list_by_owner(manager.id)
        return {
            "stats": {
                "products": product_count,
                "orders": order_count,
                "low_stock_products": len(low_stock),
                "shops": len(owned_shops),
            },
            "shops": [
                {"id": str(s.id), "name": s.name, "slug": s.slug, "status": s.status, "category": s.category}
                for s in owned_shops
            ],
            "low_stock": low_stock,
            "recent_orders": [],
        }

    # ── Products (scoped by shop) ─────────────────────────────────

    async def list_products(self, manager: Account) -> list[dict]:
        shop_ids = await self._get_shop_ids(manager.id)
        if not shop_ids:
            return []

        result = await self.db.execute(
            text(
                "SELECT p.id, p.name, p.slug, p.price, p.available_item_count, "
                "p.status, pc.name as category_name, "
                "ARRAY(SELECT pv.name FROM product_variants pv WHERE pv.product_id = p.id) as variants "
                "FROM products p "
                "JOIN shop_products sp ON sp.product_id = p.id "
                "LEFT JOIN product_categories pc ON pc.id = p.category_id "
                "WHERE sp.shop_id = ANY(:sids) "
                "ORDER BY p.created_at DESC"
            ),
            {"sids": shop_ids},
        )
        return [
            {
                "id": str(row[0]), "name": row[1], "slug": row[2],
                "price": float(row[3]), "available_item_count": row[4],
                "status": row[5], "category": row[6] or "",
                "variants": len(row[7]) if row[7] else 0,
            }
            for row in result
        ]

    async def create_product(self, manager: Account, payload: dict) -> dict:
        shop_id = payload.get("shop_id")
        if not shop_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="shop_id is required.")

        shop = await self.shops.get_by_id(uuid.UUID(shop_id))
        if shop is None or shop.owner_id != manager.id or shop.status != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shop not found or not active.")

        import hashlib
        import re

        slug_base = re.sub(r"[^a-z0-9]+", "-", payload["name"].lower()).strip("-")
        product_hash = hashlib.sha256(f"{payload['name']}::{payload.get('category', {}).get('name', '')}".encode()).hexdigest()

        product = Product(
            name=payload["name"],
            slug=slug_base,
            product_hash=product_hash,
            description=payload.get("description", ""),
            price=payload["price"],
            available_item_count=payload.get("available_item_count", 0),
            status="active",
        )
        if payload.get("category", {}).get("name"):
            from online_shopping.models.category import ProductCategory
            cat_result = await self.db.execute(
                select(ProductCategory).where(ProductCategory.name == payload["category"]["name"])
            )
            cat = cat_result.scalars().first()
            if cat:
                product.category_id = cat.id

        self.db.add(product)
        await self.db.flush()

        # Bind to shop
        from online_shopping.models.shop import ShopProduct
        self.db.add(ShopProduct(shop_id=shop.id, product_id=product.id))

        # Create default variant
        variant = ProductVariant(
            product_id=product.id,
            variant_id_str=f"var_{product.id}",
            name="Default",
            sku=f"SKU-{product.id}"[:64],
            price=payload["price"],
            inventory_count=payload.get("available_item_count", 0),
        )
        self.db.add(variant)
        await self.db.commit()

        return {"id": str(product.id), "name": product.name, "slug": product.slug, "status": product.status, "shop_id": str(shop.id)}

    async def update_product(self, manager: Account, product_id: uuid.UUID, payload: dict) -> dict:
        # Verify product belongs to manager's shop
        result = await self.db.execute(
            text(
                "SELECT p.id FROM products p "
                "JOIN shop_products sp ON sp.product_id = p.id "
                "JOIN shops s ON s.id = sp.shop_id "
                "WHERE p.id = :pid AND s.owner_id = :oid"
            ),
            {"pid": product_id, "oid": manager.id},
        )
        if result.fetchone() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in your shops.")

        product = await self.db.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        for field in ("name", "description", "price", "available_item_count", "status"):
            if field in payload and payload[field] is not None:
                setattr(product, field, payload[field])
        await self.db.commit()
        return {"id": str(product.id), "name": product.name, "status": product.status}

    # ── Orders (scoped by shop) ───────────────────────────────────

    async def list_orders(self, manager: Account) -> list[dict]:
        shop_ids = await self._get_shop_ids(manager.id)
        if not shop_ids:
            return []

        result = await self.db.execute(
            text(
                "SELECT DISTINCT o.order_number, o.status, o.order_date, o.email, "
                "SUM(oi.price * oi.quantity) as total, "
                "COUNT(oi.id) as item_count "
                "FROM orders o "
                "JOIN order_items oi ON oi.order_id = o.id "
                "WHERE oi.shop_id = ANY(:sids) "
                "GROUP BY o.id "
                "ORDER BY o.created_at DESC "
                "LIMIT 50"
            ),
            {"sids": shop_ids},
        )
        return [
            {
                "order_number": row[0], "status": row[1],
                "order_date": row[2].isoformat() if row[2] else None,
                "email": row[3],
                "total": float(row[4]), "items_count": row[5],
            }
            for row in result
        ]

    async def get_manager_order_detail(self, manager: Account, order_number: str) -> dict:
        """Get order detail with only items from this manager's shops."""
        shop_ids = await self._get_shop_ids(manager.id)
        if not shop_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        order = await self.db.execute(
            select(Order).options(selectinload(Order.items), selectinload(Order.payments))
            .where(Order.order_number == order_number)
        )
        order = order.scalars().first()
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        # Filter to only this manager's items
        my_items = [oi for oi in order.items if oi.shop_id in shop_ids]
        if not my_items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No items from your shops in this order.")

        return {
            "order_number": order.order_number,
            "status": order.status,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "email": order.email,
            "items": [
                {"id": str(oi.id), "product_name": oi.product_name, "quantity": oi.quantity,
                 "price": float(oi.price), "shop_name": oi.shop_name}
                for oi in my_items
            ],
            "payment": order.payments[0].status if order.payments else "pending",
        }

    # ── Inventory ──────────────────────────────────────────────────

    async def update_inventory(self, manager: Account, variant_id: uuid.UUID, inventory_count: int) -> dict:
        result = await self.db.execute(
            text(
                "SELECT pv.id FROM product_variants pv "
                "JOIN shop_products sp ON sp.product_id = pv.product_id "
                "JOIN shops s ON s.id = sp.shop_id "
                "WHERE pv.id = :vid AND s.owner_id = :oid"
            ),
            {"vid": variant_id, "oid": manager.id},
        )
        if result.fetchone() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found in your shops.")

        variant = await self.db.get(ProductVariant, variant_id)
        variant.inventory_count = inventory_count
        await self.db.commit()
        return {"id": str(variant.id), "name": variant.name, "sku": variant.sku, "inventory_count": variant.inventory_count}

    # ── Shipments ──────────────────────────────────────────────────

    async def create_shipment(self, manager: Account, order_number: str, payload: dict) -> dict:
        shop_ids = await self._get_shop_ids(manager.id)
        if not shop_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active shops.")

        order_result = await self.db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.order_number == order_number)
        )
        order = order_result.scalars().first()
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        # Verify order contains this manager's products
        my_shop_ids = set(shop_ids)
        order_shop_ids = {oi.shop_id for oi in order.items if oi.shop_id}
        if not my_shop_ids.intersection(order_shop_ids):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Order does not contain items from your shops.")

        # Create shipment for each of this manager's shops in the order
        shipments = []
        for sid in my_shop_ids.intersection(order_shop_ids):
            shipment = Shipment(
                order_id=order.id,
                shop_id=sid,
                status="shipped",
                carrier=payload.get("carrier"),
                tracking_number=payload.get("tracking_number"),
                tracking_url=payload.get("tracking_url"),
            )
            self.db.add(shipment)
            shipments.append(shipment)

        # Advance order status
        order.status = "processing"

        await self.db.commit()
        return {
            "shipments": [
                {"id": str(s.id), "status": s.status, "carrier": s.carrier, "tracking_number": s.tracking_number}
                for s in shipments
            ],
            "order_status": order.status,
        }

    async def list_shipments(self, manager: Account) -> list[dict]:
        shop_ids = await self._get_shop_ids(manager.id)
        if not shop_ids:
            return []
        result = await self.db.execute(
            select(Shipment).where(Shipment.shop_id.in_(shop_ids)).order_by(Shipment.created_at.desc()).limit(50)
        )
        return [
            {"id": str(s.id), "order_id": str(s.order_id), "status": s.status,
             "carrier": s.carrier, "tracking_number": s.tracking_number,
             "created_at": s.created_at.isoformat() if s.created_at else None}
            for s in result.scalars().all()
        ]

    # ── Income ─────────────────────────────────────────────────────

    async def income(self, manager: Account) -> dict:
        shop_ids = await self._get_shop_ids(manager.id)
        if not shop_ids:
            return {"total_income": 0, "pending_income": 0, "by_shop": []}

        # Paid income (orders with completed payment)
        paid_result = await self.db.execute(
            text(
                "SELECT COALESCE(SUM(oi.price * oi.quantity), 0) "
                "FROM order_items oi "
                "JOIN orders o ON o.id = oi.order_id "
                "JOIN payments pay ON pay.order_id = o.id "
                "WHERE oi.shop_id = ANY(:sids) AND pay.status = 'completed'"
            ),
            {"sids": shop_ids},
        )
        total_income = float(paid_result.scalar() or 0)

        # Pending income
        pending_result = await self.db.execute(
            text(
                "SELECT COALESCE(SUM(oi.price * oi.quantity), 0) "
                "FROM order_items oi "
                "JOIN orders o ON o.id = oi.order_id "
                "JOIN payments pay ON pay.order_id = o.id "
                "WHERE oi.shop_id = ANY(:sids) AND pay.status = 'pending'"
            ),
            {"sids": shop_ids},
        )
        pending_income = float(pending_result.scalar() or 0)

        # By shop
        by_shop_result = await self.db.execute(
            text(
                "SELECT s.name, COALESCE(SUM(oi.price * oi.quantity), 0) "
                "FROM order_items oi "
                "JOIN shops s ON s.id = oi.shop_id "
                "JOIN payments pay ON pay.order_id = oi.order_id "
                "WHERE oi.shop_id = ANY(:sids) AND pay.status = 'completed' "
                "GROUP BY s.id, s.name"
            ),
            {"sids": shop_ids},
        )
        by_shop = [{"shop": row[0], "income": float(row[1])} for row in by_shop_result]

        return {"total_income": total_income, "pending_income": pending_income, "by_shop": by_shop}

    # ── Reports ────────────────────────────────────────────────────

    async def reports(self, manager: Account) -> dict:
        shop_ids = await self._get_shop_ids(manager.id)
        if not shop_ids:
            return {"top_products": [], "low_stock": [], "recent_orders": []}

        top_result = await self.db.execute(
            text(
                "SELECT oi.product_name, SUM(oi.quantity) as sold "
                "FROM order_items oi "
                "WHERE oi.shop_id = ANY(:sids) "
                "GROUP BY oi.product_name "
                "ORDER BY sold DESC LIMIT 10"
            ),
            {"sids": shop_ids},
        )
        top_products = [{"name": row[0], "sold": row[1]} for row in top_result]

        low_result = await self.db.execute(
            text(
                "SELECT p.name, p.available_item_count "
                "FROM products p JOIN shop_products sp ON sp.product_id = p.id "
                "WHERE sp.shop_id = ANY(:sids) AND p.available_item_count <= 5 "
                "ORDER BY p.available_item_count ASC LIMIT 10"
            ),
            {"sids": shop_ids},
        )
        low_stock = [{"name": row[0], "stock": row[1]} for row in low_result]

        recent_result = await self.db.execute(
            text(
                "SELECT DISTINCT o.order_number, o.status, o.order_date "
                "FROM orders o JOIN order_items oi ON oi.order_id = o.id "
                "WHERE oi.shop_id = ANY(:sids) "
                "ORDER BY o.created_at DESC LIMIT 10"
            ),
            {"sids": shop_ids},
        )
        recent = [
            {"order_number": row[0], "status": row[1],
             "date": row[2].isoformat() if row[2] else None}
            for row in recent_result
        ]

        return {"top_products": top_products, "low_stock": low_stock, "recent_orders": recent}

    # ── Create shop ────────────────────────────────────────────────

    async def create_shop(self, manager: Account, payload: dict) -> dict:
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", payload["name"].lower()).strip("-") or "shop"
        shop = Shop(
            name=payload["name"], slug=slug,
            description=payload.get("description", ""),
            owner_id=manager.id, status="pending",
            category=payload.get("category"),
        )
        await self.shops.save(shop)
        await self.db.commit()
        return {"id": str(shop.id), "name": shop.name, "slug": shop.slug, "status": shop.status}

    async def update_shop(self, manager: Account, shop_id: uuid.UUID, payload: dict) -> dict:
        shop = await self.shops.get_by_id(shop_id)
        if shop is None or shop.owner_id != manager.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found.")
        allowed = {"name", "description", "category", "logo_url", "banner_url"}
        for key in allowed:
            if key in payload and payload[key] is not None:
                setattr(shop, key, payload[key])
        if "name" in payload:
            import re
            shop.slug = re.sub(r"[^a-z0-9]+", "-", payload["name"].lower()).strip("-")
        await self.db.commit()
        return {"id": str(shop.id), "name": shop.name, "slug": shop.slug, "status": shop.status}
