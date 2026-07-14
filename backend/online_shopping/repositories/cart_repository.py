from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from online_shopping.models.cart import CartItem, ShoppingCart
from online_shopping.models.product import Product
from online_shopping.models.product_variant import ProductVariant


class CartRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_default_cart(
        self, email: str | None = None, cart_id: str | None = None
    ) -> ShoppingCart:
        cart = await self._load_default_cart(email=email, cart_id=cart_id)
        if cart is not None:
            return cart

        cart = ShoppingCart(
            region_id="reg_cny",
            currency_code="cny",
            locale="cn",
            email=email,
        )
        self.db.add(cart)
        await self.db.flush()
        return await self.get_cart(cart.id)

    async def get_cart(self, cart_id) -> ShoppingCart:
        result = await self.db.execute(
            select(ShoppingCart)
            .options(
                joinedload(ShoppingCart.items)
                .joinedload(CartItem.variant)
                .joinedload(ProductVariant.product)
                .joinedload(Product.category),
                joinedload(ShoppingCart.items)
                .joinedload(CartItem.variant)
                .joinedload(ProductVariant.product)
                .joinedload(Product.images),
                joinedload(ShoppingCart.items)
                .joinedload(CartItem.variant)
                .joinedload(ProductVariant.product)
                .joinedload(Product.variants),
            )
            .where(ShoppingCart.id == cart_id)
            .execution_options(populate_existing=True)
        )
        return result.unique().scalars().one()

    async def _load_default_cart(
        self, email: str | None = None, cart_id: str | None = None
    ) -> ShoppingCart | None:
        # Logged-in users get exactly one active cart keyed by email. If they
        # arrive with an anonymous cart_id, attach that cart only when no
        # account cart exists yet.
        if email:
            result = await self.db.execute(
                select(ShoppingCart)
                .where(ShoppingCart.email == email)
                .order_by(ShoppingCart.created_at.desc())
                .limit(1)
            )
            cart = result.scalars().first()
            if cart is not None:
                return await self.get_cart(cart.id)

            if cart_id:
                try:
                    cid = uuid.UUID(cart_id)
                except (ValueError, TypeError):
                    cid = None
                if cid:
                    result = await self.db.execute(
                        select(ShoppingCart).where(ShoppingCart.id == cid)
                    )
                    cart = result.scalars().first()
                    if cart is not None:
                        cart.email = email
                        await self.db.flush()
                        return await self.get_cart(cart.id)

            return None

        # 1) Specific cart_id takes priority (guest isolation)
        if cart_id:
            try:
                cid = uuid.UUID(cart_id)
            except (ValueError, TypeError):
                cid = None
            if cid:
                result = await self.db.execute(
                    select(ShoppingCart).where(ShoppingCart.id == cid)
                )
                cart = result.scalars().first()
                if cart is not None:
                    return await self.get_cart(cart.id)
                # cart_id not found — fall through to create new one

        # 2) Logged-in user: match by email
        if email:
            result = await self.db.execute(
                select(ShoppingCart)
                .where(ShoppingCart.email == email)
                .order_by(ShoppingCart.created_at.desc())
                .limit(1)
            )
        else:
            # 3) Anonymous — NO global shared cart; always create new
            return None

        cart = result.scalars().first()
        if cart is None:
            return None
        return await self.get_cart(cart.id)

    async def find_item(self, cart: ShoppingCart, identity: str) -> CartItem | None:
        folded = identity.casefold()
        for item in cart.items:
            product = item.variant.product
            identifiers = {
                str(item.id).casefold(),
                str(item.product_variant_id).casefold(),
                item.variant.variant_id_str.casefold(),
                item.variant.sku.casefold(),
                product.name.casefold(),
                product.slug.casefold(),
            }
            if folded in identifiers:
                return item
        return None

    async def add_item(self, cart: ShoppingCart, variant: ProductVariant, quantity: int) -> CartItem:
        existing = await self.find_item(cart, str(variant.id))
        if existing:
            existing.quantity += quantity
            await self.db.flush()
            return existing

        item = CartItem(
            cart_id=cart.id,
            product_variant_id=variant.id,
            quantity=quantity,
            price=variant.price,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def delete_item(self, item: CartItem) -> None:
        await self.db.delete(item)
        await self.db.flush()

    async def clear(self, cart: ShoppingCart) -> None:
        for item in list(cart.items):
            await self.db.delete(item)
        await self.db.flush()

    async def save(self, cart: ShoppingCart) -> ShoppingCart:
        """Persist changes to a cart (address, shipping, etc.)."""
        await self.db.flush()
        return await self.get_cart(cart.id)
