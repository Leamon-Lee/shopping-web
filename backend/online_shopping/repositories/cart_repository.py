from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.cart import CartItem, ShoppingCart
from online_shopping.models.product import Product
from online_shopping.models.product_variant import ProductVariant


class CartRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_default_cart(self, email: str | None = None) -> ShoppingCart:
        cart = await self._load_default_cart(email=email)
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
                selectinload(ShoppingCart.items)
                .selectinload(CartItem.variant)
                .selectinload(ProductVariant.product)
                .selectinload(Product.category),
                selectinload(ShoppingCart.items)
                .selectinload(CartItem.variant)
                .selectinload(ProductVariant.product)
                .selectinload(Product.images),
                selectinload(ShoppingCart.items)
                .selectinload(CartItem.variant)
                .selectinload(ProductVariant.product)
                .selectinload(Product.variants),
            )
            .where(ShoppingCart.id == cart_id)
        )
        return result.scalars().one()

    async def _load_default_cart(self, email: str | None = None) -> ShoppingCart | None:
        if email:
            result = await self.db.execute(
                select(ShoppingCart)
                .where(ShoppingCart.email == email)
                .order_by(ShoppingCart.created_at.desc())
                .limit(1)
            )
        else:
            result = await self.db.execute(
                select(ShoppingCart)
                .where(ShoppingCart.customer_id.is_(None), ShoppingCart.email.is_(None))
                .order_by(ShoppingCart.created_at.asc())
                .limit(1)
            )
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
