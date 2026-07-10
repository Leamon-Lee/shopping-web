from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.models.cart import ShoppingCart
from online_shopping.models.product_variant import ProductVariant
from online_shopping.repositories.cart_repository import CartRepository
from online_shopping.repositories.catalog_repository import CatalogRepository


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.carts = CartRepository(db)
        self.catalog = CatalogRepository(db)

    async def get_cart(self, email: str | None = None) -> ShoppingCart:
        return await self.carts.get_default_cart(email=email)

    async def add_item(self, identity: str, quantity: int, email: str | None = None) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email)
        variant = await self._resolve_variant(identity)
        if variant.inventory_count < quantity and not variant.allows_backorder:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient inventory.")

        await self.carts.add_item(cart, variant, quantity)
        await self.db.commit()
        return await self.carts.get_cart(cart.id)

    async def update_item(self, identity: str, quantity: int, email: str | None = None) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email)
        item = await self.carts.find_item(cart, identity)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
        if item.variant.inventory_count < quantity and not item.variant.allows_backorder:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient inventory.")

        item.quantity = quantity
        await self.db.commit()
        return await self.carts.get_cart(cart.id)

    async def remove_item(self, identity: str, email: str | None = None) -> ShoppingCart:
        cart = await self.carts.get_default_cart(email=email)
        item = await self.carts.find_item(cart, identity)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")

        await self.carts.delete_item(item)
        await self.db.commit()
        return await self.carts.get_cart(cart.id)

    async def clear_cart(self, cart: ShoppingCart) -> None:
        await self.carts.clear(cart)

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
