from __future__ import annotations

import re

from online_shopping.api.mappers import product_to_out
from online_shopping.repositories.catalog_repository import CatalogRepository
from online_shopping.repositories.marketplace_repository import MarketplaceRepository


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "shop"


def stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


SECTION_PRODUCT_CAP = 8
DEFAULT_PAGE_LIMIT = 24
MAX_PAGE_LIMIT = 60


class MarketplaceService:
    def __init__(
        self,
        catalog_repository: CatalogRepository,
        marketplace_repository: MarketplaceRepository,
    ):
        self.catalog_repository = catalog_repository
        self.marketplace_repository = marketplace_repository

    async def hall_payload(self) -> dict:
        """Return marketplace metadata, shops, categories, and capped sections.

        The full product catalog is no longer included — the frontend fetches
        paginated product batches via GET /hall/products.
        """
        shop_summaries = await self.marketplace_repository.list_shop_summaries()
        product_shops = await self.marketplace_repository.product_shop_map()

        # Build category list from all shop categories
        category_names: list[str] = []
        for shop in shop_summaries:
            category_names.extend(shop.categories)

        shops = [
            {
                "id": str(shop.id),
                "name": shop.name,
                "slug": slugify(shop.name),
                "product_count": shop.product_count,
                "categories": list(shop.categories),
            }
            for shop in shop_summaries
        ]

        # Build capped sections: up to SECTION_PRODUCT_CAP products per shop
        sections: list[dict] = []
        for shop in shops:
            shop_products = await self.catalog_repository.list_products_paginated(
                shop=shop["slug"],
                limit=SECTION_PRODUCT_CAP,
                offset=0,
            )
            if shop_products:
                enriched = []
                for product in shop_products:
                    payload = product_to_out(product).model_dump()
                    shop_meta = product_shops.get(str(product.id), {})
                    payload["shop"] = shop_meta
                    enriched.append(payload)
                sections.append({
                    "title": shop["name"],
                    "slug": shop["slug"],
                    "shop": shop,
                    "products": enriched,
                })

        # Marketplace-level stats
        product_count = sum(shop["product_count"] for shop in shops)

        return {
            "route": "/hall",
            "shops": shops,
            "categories": [
                {"name": name, "slug": slugify(name)}
                for name in stable_unique(category_names)
            ],
            "sections": sections,
            "product_count": product_count,
            "shop_count": len(shops),
            "category_count": len(stable_unique(category_names)),
        }

    async def hall_products_paginated(
        self,
        *,
        q: str | None = None,
        shop: str | None = None,
        category: str | None = None,
        limit: int = DEFAULT_PAGE_LIMIT,
        offset: int = 0,
    ) -> dict:
        """Return a paginated page of products with marketplace shop metadata."""
        limit = max(1, min(limit, MAX_PAGE_LIMIT))
        offset = max(0, offset)

        products = await self.catalog_repository.list_products_paginated(
            shop=shop,
            q=q,
            category=category,
            limit=limit,
            offset=offset,
        )
        total = await self.catalog_repository.count_products(
            shop=shop,
            q=q,
            category=category,
        )

        product_shops = await self.marketplace_repository.product_shop_map()

        enriched = []
        for product in products:
            payload = product_to_out(product).model_dump()
            shop_meta = product_shops.get(str(product.id), {})
            payload["shop"] = shop_meta
            enriched.append(payload)

        return {
            "products": enriched,
            "count": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        }
