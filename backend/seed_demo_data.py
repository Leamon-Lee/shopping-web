"""Seed demo data for manager dashboard / My Shops analytics demonstration.

Usage:
    python seed_demo_data.py

Creates:
  - A manager account (manager@demo.com / demo123)
  - 3 shops with different categories
  - Products assigned to shops
  - Orders for the last 7 days (varied volumes per shop)
  - Orders for the same period last year (for prediction feature)
"""

import asyncio
import hashlib
import random
import re
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

import bcrypt
from sqlalchemy import select, func

from online_shopping.database import async_session
from online_shopping.models.account import Account
from online_shopping.models.category import ProductCategory
from online_shopping.models.order import Order, OrderItem
from online_shopping.models.product import Product
from online_shopping.models.shop import Shop, ShopProduct

# ── Config ────────────────────────────────────────────────────────────

MANAGER_EMAIL = "manager@demo.com"
MANAGER_PASSWORD = "demo123"
MANAGER_USERNAME = "demomanager"

SHOPS = [
    {"name": "TechGear Pro", "category": "Electronics", "desc": "Premium electronics and gadgets"},
    {"name": "HomeStyle Living", "category": "Home & Kitchen", "desc": "Modern home essentials and decor"},
    {"name": "FashionHub", "category": "Clothing", "desc": "Trendy apparel and accessories"},
]

NUM_CUSTOMERS = 10
ORDERS_LAST_7_DAYS = {
    # shop_name: orders_per_day (random variation added)
    "TechGear Pro": (6, 10),       # ~50 orders, highest volume
    "HomeStyle Living": (3, 7),    # ~35 orders, medium
    "FashionHub": (2, 5),          # ~25 orders, lowest
}
LAST_YEAR_SAME_PERIOD_ORDERS = {
    "TechGear Pro": (4, 8),
    "HomeStyle Living": (2, 5),
    "FashionHub": (1, 4),
}

# ── Helpers ────────────────────────────────────────────────────────────

def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def get_or_create_categories(db, category_names: list[str]) -> dict:
    """Get existing categories or create them. Returns {name: ProductCategory}."""
    result = {}
    for name in category_names:
        stmt = select(ProductCategory).where(ProductCategory.name == name)
        r = await db.execute(stmt)
        cat = r.scalars().first()
        if cat is None:
            cat = ProductCategory(name=name, description=f"{name} products")
            db.add(cat)
            await db.flush()
        result[name] = cat
    return result


# ── Main seed logic ───────────────────────────────────────────────────

async def seed_demo():
    async with async_session() as db:
        # ── 0. Clean up old demo data (respect FK order) ─────────────
        from online_shopping.models.product_variant import ProductVariant
        from online_shopping.models.product_image import ProductImage

        print("Cleaning old demo data...")
        # Delete demo orders first (FK to accounts)
        for pattern in ["DEMO-%", "HIST-%"]:
            orders_q = await db.execute(
                select(Order).where(Order.order_number.like(pattern))
            )
            for o in orders_q.scalars().all():
                await db.execute(OrderItem.__table__.delete().where(OrderItem.order_id == o.id))
                await db.delete(o)
        await db.flush()
        print("  Deleted old demo orders.")

        # Delete demo shops and their product assignments
        demo_shop_names = [s["name"] for s in SHOPS]
        for sname in demo_shop_names:
            existing = await db.execute(select(Shop).where(Shop.name == sname))
            shop = existing.scalars().first()
            if shop:
                await db.execute(ShopProduct.__table__.delete().where(ShopProduct.shop_id == shop.id))
                await db.delete(shop)
        print("  Deleted old demo shops.")

        # Delete demo accounts (manager + customers)
        demo_emails = [MANAGER_EMAIL] + [f"customer{i+1}@demo.com" for i in range(NUM_CUSTOMERS)]
        for email in demo_emails:
            existing = await db.execute(select(Account).where(Account.email == email))
            acc = existing.scalars().first()
            if acc:
                # Delete orders with explicit query (avoid lazy loading)
                acc_orders = await db.execute(
                    select(Order).where(Order.account_id == acc.id)
                )
                for o in acc_orders.scalars().all():
                    await db.execute(OrderItem.__table__.delete().where(OrderItem.order_id == o.id))
                    await db.delete(o)
                await db.delete(acc)
        await db.flush()
        print("  Cleaned up old demo accounts.")

        # Ensure products exist (skip product seed - products should already exist)
        all_products = (await db.execute(select(Product))).scalars().all()
        if not all_products:
            print("No products found in database. Cannot seed demo data.")
            print("Please seed products first, then run this script again.")
            return
        print(f"  Found {len(all_products)} existing products — using them.")

        # ── 1. Create manager account ──────────────────────────────────
        existing = await db.execute(
            select(Account).where(Account.email == MANAGER_EMAIL)
        )
        manager = existing.scalars().first()
        if manager is None:
            manager = Account(
                user_name=MANAGER_USERNAME,
                password_hash=hash_pw(MANAGER_PASSWORD),
                email=MANAGER_EMAIL,
                first_name="Demo",
                last_name="Manager",
                role="manager",
                status="active",
            )
            db.add(manager)
            await db.flush()
            print(f"Created manager: {MANAGER_EMAIL} / {MANAGER_PASSWORD}")
        else:
            print(f"Manager already exists: {MANAGER_EMAIL}")

        # ── 2. Create shops ───────────────────────────────────────────
        shop_objs = {}
        for si, sdata in enumerate(SHOPS):
            existing_shop = await db.execute(
                select(Shop).where(Shop.name == sdata["name"])
            )
            shop = existing_shop.scalars().first()
            if shop is None:
                shop = Shop(
                    name=sdata["name"],
                    slug=slugify(sdata["name"]),
                    description=sdata["desc"],
                    owner_id=manager.id,
                    status="active",
                    category=sdata["category"],
                )
                db.add(shop)
                await db.flush()
                print(f"Created shop: {sdata['name']}")
            shop_objs[sdata["name"]] = shop

        # ── 3. Group products by category ─────────────────────────
        cats_by_name = {}
        for p in all_products:
            await db.refresh(p, ["category"])
            cname = p.category.name if p.category else "Uncategorized"
            cats_by_name.setdefault(cname, []).append(p)

        print(f"Found {len(all_products)} products across {len(cats_by_name)} categories.")

        # ── 4. Assign products to shops ───────────────────────────────
        shop_product_map = {
            "TechGear Pro": ["Electronics", "Automotive", "Office Supplies", "Books"],
            "HomeStyle Living": ["Home & Kitchen", "Groceries", "Beauty & Health", "Books"],
            "FashionHub": ["Clothing", "Sports & Outdoors", "Beauty & Health", "Toys & Games"],
        }

        all_shop_products = {
            "TechGear Pro": [],
            "HomeStyle Living": [],
            "FashionHub": [],
        }

        for shop_name, cat_names in shop_product_map.items():
            shop = shop_objs[shop_name]
            for cname in cat_names:
                products = cats_by_name.get(cname, [])
                for p in products:
                    # Check if already linked
                    existing_link = await db.execute(
                        select(ShopProduct).where(
                            ShopProduct.shop_id == shop.id,
                            ShopProduct.product_id == p.id,
                        )
                    )
                    if existing_link.scalars().first() is None:
                        db.add(ShopProduct(shop_id=shop.id, product_id=p.id))
                    all_shop_products[shop_name].append(p)

        await db.flush()
        for sname, plist in all_shop_products.items():
            print(f"  {sname}: {len(plist)} products")

        # ── 5. Create customer accounts for orders ────────────────────
        customers = []
        for i in range(NUM_CUSTOMERS):
            email = f"customer{i+1}@demo.com"
            existing_cust = await db.execute(select(Account).where(Account.email == email))
            cust = existing_cust.scalars().first()
            if cust is None:
                cust = Account(
                    user_name=f"democustomer{i+1}",
                    password_hash=hash_pw("demo123"),
                    email=email,
                    first_name=f"Customer{i+1}",
                    last_name="Demo",
                    role="customer",
                    status="active",
                )
                db.add(cust)
                await db.flush()
            customers.append(cust)
        print(f"Have {len(customers)} customer accounts.")

        # ── 6. Generate orders for last 7 days ────────────────────────
        today = datetime.utcnow().date()
        order_count = 0

        for day_offset in range(6, -1, -1):  # 6 days ago to today
            order_date = today - timedelta(days=day_offset)

            for shop_name, (min_orders, max_orders) in ORDERS_LAST_7_DAYS.items():
                shop = shop_objs[shop_name]
                num_orders = random.randint(min_orders, max_orders)
                products_pool = all_shop_products[shop_name]

                if not products_pool:
                    continue

                for _ in range(num_orders):
                    customer = random.choice(customers)
                    order_number = f"DEMO-{order_date.strftime('%Y%m%d')}-{random.randint(10000, 99999):05d}"

                    order = Order(
                        account_id=customer.id,
                        order_number=order_number,
                        status=random.choice(["completed", "completed", "completed", "processing", "shipped"]),
                        order_date=datetime(order_date.year, order_date.month, order_date.day,
                                             random.randint(8, 20), random.randint(0, 59)),
                    )
                    db.add(order)
                    await db.flush()

                    # 1-4 items per order
                    num_items = random.randint(1, min(4, len(products_pool)))
                    chosen = random.sample(products_pool, num_items)
                    for prod in chosen:
                        qty = random.randint(1, 3)
                        db.add(OrderItem(
                            order_id=order.id,
                            product_id=prod.id,
                            product_name=prod.name,
                            quantity=qty,
                            price=float(prod.price),
                        ))
                    order_count += 1

        print(f"Created {order_count} orders for last 7 days.")

        # ── 7. Generate orders for same period last year (predictions) ─
        last_year = today.replace(year=today.year - 1)
        hist_order_count = 0

        for day_offset in range(6, -1, -1):
            order_date = last_year - timedelta(days=day_offset)

            for shop_name, (min_orders, max_orders) in LAST_YEAR_SAME_PERIOD_ORDERS.items():
                shop = shop_objs[shop_name]
                num_orders = random.randint(min_orders, max_orders)
                products_pool = all_shop_products[shop_name]

                if not products_pool:
                    continue

                for _ in range(num_orders):
                    customer = random.choice(customers)
                    order_number = f"HIST-{order_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

                    order = Order(
                        account_id=customer.id,
                        order_number=order_number,
                        status="completed",
                        order_date=datetime(order_date.year, order_date.month, order_date.day,
                                             random.randint(8, 20), random.randint(0, 59)),
                    )
                    db.add(order)
                    await db.flush()

                    num_items = random.randint(1, min(3, len(products_pool)))
                    chosen = random.sample(products_pool, num_items)
                    for prod in chosen:
                        qty = random.randint(1, 3)
                        db.add(OrderItem(
                            order_id=order.id,
                            product_id=prod.id,
                            product_name=prod.name,
                            quantity=qty,
                            price=float(prod.price),
                        ))
                    hist_order_count += 1

        print(f"Created {hist_order_count} historical orders for last year same period.")

        # ── 8. Bonus: spread orders across 30 days for admin analytics ─
        spread_count = 0
        for day_offset in range(29, 6, -1):  # 29 to 7 days ago (additional days beyond the 7-day window)
            order_date = today - timedelta(days=day_offset)

            for shop_name, (min_orders, max_orders) in ORDERS_LAST_7_DAYS.items():
                shop = shop_objs[shop_name]
                num_orders = random.randint(max(1, min_orders - 2), max(1, max_orders - 3))
                products_pool = all_shop_products[shop_name]
                if not products_pool:
                    continue

                for _ in range(num_orders):
                    customer = random.choice(customers)
                    order_number = f"DEMO-{order_date.strftime('%Y%m%d')}-{random.randint(10000, 99999):05d}"
                    order = Order(
                        account_id=customer.id,
                        order_number=order_number,
                        status=random.choice(["completed", "completed", "completed", "processing"]),
                        order_date=datetime(order_date.year, order_date.month, order_date.day,
                                             random.randint(8, 20), random.randint(0, 59)),
                    )
                    db.add(order)
                    await db.flush()
                    num_items = random.randint(1, min(4, len(products_pool)))
                    chosen = random.sample(products_pool, num_items)
                    for prod in chosen:
                        qty = random.randint(1, 3)
                        db.add(OrderItem(
                            order_id=order.id,
                            product_id=prod.id,
                            product_name=prod.name,
                            quantity=qty,
                            price=float(prod.price),
                        ))
                    spread_count += 1

        print(f"Created {spread_count} additional orders across 30-day range.")

        await db.commit()
        print("\n=== Demo data seeded successfully! ===")
        print(f"Manager login: {MANAGER_EMAIL} / {MANAGER_PASSWORD}")
        print("Admin analytics: Customer Preferences and Daily Rankings ready to demo.")
        print(f"3 shops, ~{order_count + spread_count} recent + spread orders, ~{hist_order_count} historical orders.")


if __name__ == "__main__":
    asyncio.run(seed_demo())
