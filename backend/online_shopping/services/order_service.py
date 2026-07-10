from __future__ import annotations

from itertools import count

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.api.schemas import OrderCreate
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.models.account import Account
from online_shopping.models.order import Order, OrderItem
from online_shopping.models.payment import Payment
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

    async def place_order(self, payload: OrderCreate, email: str | None = None) -> Order:
        validated_items = []
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
            cart = await self.carts.get_default_cart(email=email)
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

        order_number = payload.order_number or f"ORD-{next(_order_numbers)}"
        order = Order(
            order_number=order_number,
            status=OrderStatus.CREATED.value,
            account_id=account_id,
        )
        await self.orders.save(order)

        amount = 0.0
        for product, quantity, variant in validated_items:
            price = variant.price if variant is not None else product.price
            amount += float(price) * quantity
            if variant is not None and variant.manages_inventory and not variant.allows_backorder:
                if variant.inventory_count < quantity:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Insufficient inventory for '{product.name}'.",
                    )
                variant.inventory_count -= quantity
            self.db.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                price=price,
            ))

        payment_payload = payload.payment
        self.db.add(Payment(
            order_id=order.id,
            status=PaymentStatus.PENDING.value,
            amount=payment_payload.amount if payment_payload else round(amount, 2),
            currency=payment_payload.currency if payment_payload else "CNY",
        ))

        if cart is not None:
            await self.carts.clear(cart)

        await self.db.commit()
        created = await self.orders.get_by_number(order.order_number)
        assert created is not None
        return created
