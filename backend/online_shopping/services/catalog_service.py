"""Catalog service — orchestrates product & category operations."""

from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.schemas import CategoryOut, ProductCreate, ProductOut, ProductUpdate
from online_shopping.models.category import ProductCategory
from online_shopping.models.product import Product
from online_shopping.models.product_variant import ProductVariant
from online_shopping.repositories.catalog_repository import CatalogRepository
from online_shopping.services.hash_service import generate_product_hash


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "product"


class CatalogService:
    """Orchestrates product catalog read/write operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CatalogRepository(db)

    # ── Read ──────────────────────────────────────────────────────

    async def list_products(self, shop: str | None = None) -> list[Product]:
        return await self.repo.list_products(shop=shop)

    async def list_categories(self) -> list[ProductCategory]:
        return await self.repo.list_categories()

    async def list_category_out(self) -> list[CategoryOut]:
        categories = await self.repo.list_categories()
        return [
            CategoryOut(name=cat.name, description=cat.description)
            for cat in categories
        ]

    async def find_product(self, identity: str) -> Product | None:
        return await self.repo.find_product(identity)

    # ── Write ─────────────────────────────────────────────────────

    async def create_product(self, payload: ProductCreate) -> Product:
        """Create a product with category resolution, slug, and default variant."""
        category_name = payload.category.name
        product_hash = generate_product_hash(payload.name, category_name)

        existing = await self.repo.find_product(payload.name)
        if existing is not None:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product already exists.",
            )

        # Resolve or create category
        category = await self._resolve_category(category_name, payload.category.description)

        slug = _slugify(payload.name)
        product = Product(
            product_hash=product_hash,
            category_id=category.id,
            name=payload.name,
            slug=slug,
            description=payload.description,
            price=payload.price,
            available_item_count=payload.available_item_count,
        )
        await self.repo.save_product(product)

        # Create default variant
        self.db.add(ProductVariant(
            product_id=product.id,
            variant_id_str=f"variant_{slug}",
            name="Default Variant",
            sku=f"SKU-{slug[:48].upper()}",
            price=payload.price,
            inventory_count=payload.available_item_count,
        ))

        await self.db.commit()

        created = await self.repo.find_product(product_hash)
        assert created is not None
        return created

    async def update_product(self, product: Product, payload: ProductUpdate) -> Product:
        updates = payload.model_dump(exclude_none=True)
        return await self.repo.update_product(product, updates)

    async def delete_product(self, product: Product) -> None:
        await self.repo.delete_product(product)

    # ── Search ────────────────────────────────────────────────────

    def search(self, query: str) -> list[object]:
        """Search products — full-text search to be implemented."""
        if not query.strip():
            return []
        # TODO: Implement full-text search via CatalogRepository
        return []

    # ── Helpers ───────────────────────────────────────────────────

    async def _resolve_category(self, name: str, description: str) -> ProductCategory:
        """Find existing category by case-insensitive name or create a new one."""
        categories = await self.repo.list_categories()
        for cat in categories:
            if cat.name.casefold() == name.casefold():
                return cat

        category = ProductCategory(name=name, description=description)
        self.db.add(category)
        await self.db.flush()
        return category
