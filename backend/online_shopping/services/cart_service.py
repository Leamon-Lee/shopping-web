from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.database import async_session
from online_shopping.models.cart import ShoppingCart
from online_shopping.models.product_variant import ProductVariant
from online_shopping.repositories.cart_repository import CartRepository
from online_shopping.repositories.catalog_repository import CatalogRepository


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.carts = CartRepository(db)
        self.catalog = CatalogRepository(db)

    async def get_cart(
        self, email: str | None = None, cart_id: str | None = None
    ) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email, cart_id=cart_id)
        await self.db.commit()
        return await self._reload_cart(cart.id)

    async def add_item(
        self, identity: str, quantity: int,
        email: str | None = None, cart_id: str | None = None,
    ) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email, cart_id=cart_id)
        variant = await self._resolve_variant(identity)
        if variant.inventory_count < quantity and not variant.allows_backorder:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient inventory.")

        await self.carts.add_item(cart, variant, quantity)
        await self.db.commit()
        return await self._reload_cart(cart.id)

    async def update_item(
        self, identity: str, quantity: int,
        email: str | None = None, cart_id: str | None = None,
    ) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email, cart_id=cart_id)
        item = await self.carts.find_item(cart, identity)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
        if item.variant.inventory_count < quantity and not item.variant.allows_backorder:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient inventory.")

        item.quantity = quantity
        await self.db.commit()
        return await self._reload_cart(cart.id)

    async def remove_item(
        self, identity: str,
        email: str | None = None, cart_id: str | None = None,
    ) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email, cart_id=cart_id)
        item = await self.carts.find_item(cart, identity)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")

        await self.carts.delete_item(item)
        await self.db.commit()
        return await self._reload_cart(cart.id)

    async def set_addresses(
        self,
        shipping_address: dict,
        billing_address: dict | None = None,
        email: str | None = None,
        cart_id: str | None = None,
    ) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email, cart_id=cart_id)
        cart.shipping_address = shipping_address
        cart.billing_address = billing_address or shipping_address
        # Set email from shipping_address if provided, falling back to existing auth email
        form_email = shipping_address.get("email") or shipping_address.get("shipping_address.email", "")
        if form_email:
            cart.email = form_email
        await self.db.commit()
        return await self._reload_cart(cart.id)

    async def set_email(
        self, email_addr: str,
        existing_email: str | None = None, cart_id: str | None = None,
    ) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=existing_email, cart_id=cart_id)
        cart.email = email_addr
        await self.db.commit()
        return await self._reload_cart(cart.id)

    async def set_shipping_method(
        self, shipping_method_id: str,
        email: str | None = None, cart_id: str | None = None,
    ) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email, cart_id=cart_id)
        cart.shipping_method = {
            "id": "bsms_standard",
            "shipping_option_id": shipping_method_id,
            "name": "Standard Shipping",
            "amount": 0,
        }
        await self.db.commit()
        return await self._reload_cart(cart.id)

    async def create_payment_session(
        self, provider_id: str = "pp_system_default",
        email: str | None = None, cart_id: str | None = None,
    ) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email, cart_id=cart_id)
        cart.payment_session = {
            "id": f"paysess_{cart.id}",
            "provider_id": provider_id,
            "status": "pending",
            "amount": sum(
                (float(item.price) * item.quantity) for item in cart.items
            ),
            "currency_code": cart.currency_code,
        }
        await self.db.commit()
        return await self._reload_cart(cart.id)

    async def clear_cart(self, cart: ShoppingCart) -> None:
        await self.carts.clear(cart)

    async def _reload_cart(self, cart_id) -> ShoppingCart:
        async with async_session() as session:
            return await CartRepository(session).get_cart(cart_id)

    async def _resolve_variant(self, identity: str) -> ProductVariant:
        variant = await self.catalog.find_variant(identity)
        if variant is not None:
            return variant

        product = await self.catalog.find_product(identity)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        if not product.variants:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product has no purchasable variant.")
        return product.variants[0]
