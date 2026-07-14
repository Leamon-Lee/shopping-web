from __future__ import annotations

import secrets
from itertools import count

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.schemas import OrderCreate
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.models.account import Account
from online_shopping.models.order import Order, OrderItem
from online_shopping.models.payment import Payment
from online_shopping.models.shipment import Shipment
from online_shopping.repositories.cart_repository import CartRepository
from online_shopping.repositories.catalog_repository import CatalogRepository
from online_shopping.repositories.order_repository import OrderRepository

_order_numbers = count(1001)


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.orders = OrderRepository(db)
        self.carts = CartRepository(db)
        self.catalog = CatalogRepository(db)

    async def list_orders(self, email: str | None = None) -> list[Order]:
        return await self.orders.list_orders(email=email)

    async def get_order(self, order_number: str) -> Order | None:
        return await self.orders.get_by_number(order_number)

    async def get_order_by_token(self, order_number: str, access_token: str) -> Order | None:
        return await self.orders.get_by_number_and_token(order_number, access_token)

    async def place_order(
        self, payload: OrderCreate,
        email: str | None = None, cart_id: str | None = None,
    ) -> Order:
        import uuid as _uuid

        validated_items: list[tuple] = []
        cart = None
        if payload.items:
            for item in payload.items:
                product = await self.catalog.find_product(item.product_name)
                if product is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product '{item.product_name}' not found.",
                    )
                validated_items.append(
                    (product, item.quantity, product.variants[0] if product.variants else None)
                )
        else:
            cart = await self.carts.get_default_cart(email=email, cart_id=cart_id)
            validated_items = [
                (cart_item.variant.product, cart_item.quantity, cart_item.variant)
                for cart_item in cart.items
            ]

        if not validated_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must have at least one item.",
            )

        # Resolve account if email provided
        account_id = None
        if email:
            account_result = await self.db.execute(
                select(Account).where(Account.email == email)
            )
            account = account_result.scalars().first()
            if account:
                account_id = account.id

        # ── Fix 1: Validate every product is in an active shop ──────
        product_shop_map: dict[str, tuple[str | None, str | None]] = {}
        for product_i, _, _ in validated_items:
            shop_result = await self.db.execute(
                text("""
                    SELECT s.id::text, s.name
                    FROM shops s
                    JOIN shop_products sp ON sp.shop_id = s.id
                    WHERE sp.product_id = :pid AND s.status = 'active'
                    LIMIT 1
                """),
                {"pid": product_i.id},
            )
            row = shop_result.fetchone()
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product_i.name}' is not available in any active shop.",
                )
            product_shop_map[str(product_i.id)] = (row[0], row[1])

        # Generate guest access token
        is_guest = account_id is None
        access_token = secrets.token_urlsafe(32) if is_guest else None

        order_number = payload.order_number or f"ORD-{next(_order_numbers)}"
        order = Order(
            order_number=order_number,
            status=OrderStatus.CREATED.value,
            account_id=account_id,
            email=cart.email if cart else email,
            shipping_address=cart.shipping_address if cart else None,
            billing_address=cart.billing_address if cart else None,
            shipping_method=cart.shipping_method if cart else None,
            order_access_token=access_token,
            cart_id=_uuid.UUID(cart_id) if cart_id else None,
        )
        await self.orders.save(order)

        amount = 0.0
        # ── Fix 2: Track shop_ids per-item correctly from the iteration variable ──
        shop_ids_in_order: set[str] = set()
        for item_product, quantity, variant in validated_items:
            price = variant.price if variant is not None else item_product.price
            amount += float(price) * quantity
            if variant is not None and variant.manages_inventory and not variant.allows_backorder:
                if variant.inventory_count < quantity:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Insufficient inventory for '{item_product.name}'.",
                    )
                variant.inventory_count -= quantity

            sid, sname = product_shop_map.get(str(item_product.id), (None, None))
            shop_id = _uuid.UUID(sid) if sid else None
            if sid:
                shop_ids_in_order.add(sid)

            self.db.add(OrderItem(
                order_id=order.id,
                product_id=item_product.id,
                product_name=item_product.name,
                quantity=quantity,
                price=price,
                shop_id=shop_id,
                shop_name=sname,
            ))

        # Create payment with pending status
        payment_payload = payload.payment
        self.db.add(Payment(
            order_id=order.id,
            status=PaymentStatus.PENDING.value,
            amount=payment_payload.amount if payment_payload else round(amount, 2),
            currency=payment_payload.currency if payment_payload else "CNY",
        ))

        # ── Fix 2: Create per-shop shipment using collected shop_ids ──
        if cart and cart.shipping_method:
            for sid in shop_ids_in_order:
                self.db.add(Shipment(
                    order_id=order.id,
                    shop_id=_uuid.UUID(sid),
                    status="pending",
                    carrier=cart.shipping_method.get("name", "Standard Shipping"),
                ))

        # Clear the cart after successful order
        if cart is not None:
            await self.carts.clear(cart)

        await self.db.commit()
        created = await self.orders.get_by_number(order.order_number)
        assert created is not None
        return created
