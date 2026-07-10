from __future__ import annotations

import re
from collections import defaultdict

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


class MarketplaceService:
    def __init__(
        self,
        catalog_repository: CatalogRepository,
        marketplace_repository: MarketplaceRepository,
    ):
        self.catalog_repository = catalog_repository
        self.marketplace_repository = marketplace_repository

    async def hall_payload(self) -> dict:
        products = await self.catalog_repository.list_products()
        shop_summaries = await self.marketplace_repository.list_shop_summaries()
        product_shops = await self.marketplace_repository.product_shop_map()

        enriched_products = []
        products_by_shop: dict[str, list[dict]] = defaultdict(list)
        category_names: list[str] = []

        for product in products:
            payload = product_to_out(product).model_dump()
            shop_meta = product_shops.get(str(product.id), {})
            payload["shop"] = shop_meta
            enriched_products.append(payload)

            if shop_meta.get("shop_name"):
                products_by_shop[shop_meta["shop_name"]].append(payload)
            if product.category:
                category_names.append(product.category.name)

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

        sections = [
            {
                "title": shop["name"],
                "slug": shop["slug"],
                "shop": shop,
                "products": products_by_shop.get(shop["name"], [])[:8],
            }
            for shop in shops
            if products_by_shop.get(shop["name"])
        ]

        return {
            "route": "/hall",
            "products": enriched_products,
            "shops": shops,
            "categories": [
                {"name": name, "slug": slugify(name)}
                for name in stable_unique(category_names)
            ],
            "sections": sections,
        }
