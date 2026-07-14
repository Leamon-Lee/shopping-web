from __future__ import annotations

from sqlalchemy import String, cast, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.category import ProductCategory
from online_shopping.models.product import Product
from online_shopping.models.product_image import ProductImage
from online_shopping.models.product_variant import ProductVariant


class CatalogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_products(self, shop: str | None = None) -> list[Product]:
        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants),
            )
            .where(Product.status == "active")
            .order_by(Product.created_at.desc())
        )
        if shop:
            product_ids = await self._product_ids_for_shop(shop)
            if not product_ids:
                return []
            query = query.where(Product.id.in_(product_ids))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_products_paginated(
        self,
        *,
        shop: str | None = None,
        q: str | None = None,
        category: str | None = None,
        limit: int = 24,
        offset: int = 0,
    ) -> list[Product]:
        """Paginated product listing with optional DB-level filters."""
        product_ids: set[str] | None = None
        if shop:
            ids = await self._product_ids_for_shop(shop)
            if not ids:
                return []
            product_ids = set(ids)

        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants),
            )
            .where(Product.status == "active")
            .order_by(Product.created_at.desc())
        )

        if product_ids is not None:
            query = query.where(Product.id.in_(product_ids))

        if q:
            search_term = f"%{q.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Product.name).like(search_term),
                    func.lower(Product.description).like(search_term),
                )
            )

        if category:
            query = query.join(ProductCategory, Product.category_id == ProductCategory.id).where(
                func.lower(ProductCategory.name) == category.strip().lower()
            )

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_products(
        self,
        *,
        shop: str | None = None,
        q: str | None = None,
        category: str | None = None,
    ) -> int:
        """Count products matching the given filters."""
        product_ids: set[str] | None = None
        if shop:
            ids = await self._product_ids_for_shop(shop)
            if not ids:
                return 0
            product_ids = set(ids)

        query = select(func.count(Product.id))

        if product_ids is not None:
            query = query.where(Product.id.in_(product_ids))

        if q:
            search_term = f"%{q.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Product.name).like(search_term),
                    func.lower(Product.description).like(search_term),
                )
            )

        if category:
            query = query.join(ProductCategory, Product.category_id == ProductCategory.id).where(
                func.lower(ProductCategory.name) == category.strip().lower()
            )

        result = await self.db.execute(query)
        return result.scalar_one()

    async def _product_ids_for_shop(self, shop: str) -> list[str]:
        normalized = shop.strip().lower()
        result = await self.db.execute(
            text(
                """
                SELECT sp.product_id
                FROM shop_products sp
                JOIN shops s ON s.id = sp.shop_id
                WHERE s.status = 'active'
                  AND (
                    lower(s.name) = :shop
                    OR regexp_replace(lower(s.name), '[^a-z0-9]+', '-', 'g') = :shop
                  )
                """
            ),
            {"shop": normalized},
        )
        return [row.product_id for row in result]

    async def list_categories(self) -> list[ProductCategory]:
        result = await self.db.execute(select(ProductCategory).order_by(ProductCategory.name))
        return list(result.scalars().all())

    async def find_product(self, identity: str) -> Product | None:
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants),
            )
            .where(
                Product.status == "active",
                or_(
                    Product.name.ilike(identity),
                    Product.slug == identity,
                    Product.product_hash == identity,
                ),
            )
        )
        return result.scalars().first()

    async def find_variant(self, identity: str) -> ProductVariant | None:
        result = await self.db.execute(
            select(ProductVariant)
            .options(
                selectinload(ProductVariant.product).selectinload(Product.category),
                selectinload(ProductVariant.product).selectinload(Product.images),
                selectinload(ProductVariant.product).selectinload(Product.variants),
            )
            .where(
                or_(
                    cast(ProductVariant.id, String) == identity,
                    ProductVariant.variant_id_str == identity,
                    ProductVariant.sku == identity,
                )
            )
        )
        return result.scalars().first()

    async def save_product(self, product: Product) -> Product:
        self.db.add(product)
        await self.db.flush()
        return product

    async def save_image(self, image: ProductImage) -> ProductImage:
        self.db.add(image)
        await self.db.flush()
        return image
