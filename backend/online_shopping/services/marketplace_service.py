from __future__ import annotations

import re
import hashlib
from datetime import datetime, timezone

from online_shopping.api.mappers import product_to_out
from online_shopping.models.recommendation_result import PopularProduct
from online_shopping.models.review import Review
from online_shopping.repositories.catalog_repository import CatalogRepository
from online_shopping.repositories.marketplace_repository import MarketplaceRepository
from sqlalchemy import func, select


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
        product_categories = await self.catalog_repository.list_categories()

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
                {"name": c.name, "slug": c.name}
                for c in product_categories
            ],
            "sections": sections,
            "product_count": product_count,
            "shop_count": len(shops),
            "category_count": len(product_categories),
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

        total = await self.catalog_repository.count_products(
            shop=shop,
            q=q,
            category=category,
        )
        if q or shop or category:
            products = await self.catalog_repository.list_products_paginated(
                shop=shop,
                q=q,
                category=category,
                limit=limit,
                offset=offset,
            )
        else:
            products = await self._homepage_recommendation_page(
                limit=limit,
                offset=offset,
                total=total,
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

    async def _homepage_recommendation_page(
        self,
        *,
        limit: int,
        offset: int,
        total: int,
    ):
        """Rank the unfiltered homepage feed with recommendations and rotation."""
        if total <= 0:
            return []

        products = await self.catalog_repository.list_products_paginated(
            limit=total,
            offset=0,
        )
        product_ids = [product.id for product in products]
        if not product_ids:
            return []

        db = self.catalog_repository.db
        popular_rows = await db.execute(
            select(
                PopularProduct.product_id,
                func.max(PopularProduct.score),
                func.min(PopularProduct.rank),
            )
            .where(PopularProduct.product_id.in_(product_ids))
            .group_by(PopularProduct.product_id)
        )
        popular_by_product = {
            str(product_id): {"score": float(score or 0), "rank": int(rank or 9999)}
            for product_id, score, rank in popular_rows
        }

        review_rows = await db.execute(
            select(
                Review.product_id,
                func.avg(Review.rating),
                func.count(Review.id),
            )
            .where(Review.product_id.in_(product_ids))
            .group_by(Review.product_id)
        )
        reviews_by_product = {
            str(product_id): {"avg": float(avg or 0), "count": int(count or 0)}
            for product_id, avg, count in review_rows
        }

        rotation_seed = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        ranked = sorted(
            products,
            key=lambda product: self._homepage_score(
                product,
                popular_by_product.get(str(product.id), {}),
                reviews_by_product.get(str(product.id), {}),
                rotation_seed,
            ),
            reverse=True,
        )
        return ranked[offset : offset + limit]

    @staticmethod
    def _homepage_score(product, popular: dict, reviews: dict, rotation_seed: str) -> float:
        """Blend recommendation quality with deterministic hourly variety."""
        popular_score = float(popular.get("score") or 0)
        rank = int(popular.get("rank") or 9999)
        rank_boost = max(0.0, 12.0 - min(rank, 12)) / 12.0

        avg_rating = float(reviews.get("avg") or 0)
        review_count = int(reviews.get("count") or 0)
        rating_score = 0.0
        if review_count:
            rating_score = (avg_rating - 3.0) * min(review_count, 20) / 5.0

        age_score = 0.0
        if product.created_at:
            created_at = product.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age_days = max(0.0, (datetime.now(timezone.utc) - created_at).total_seconds() / 86400.0)
            age_score = max(0.0, 1.0 - min(age_days, 30.0) / 30.0)

        digest = hashlib.sha256(f"{rotation_seed}:{product.id}".encode("utf-8")).hexdigest()
        rotation = int(digest[:8], 16) / 0xFFFFFFFF

        return (
            popular_score * 1.0
            + rank_boost * 2.0
            + rating_score * 2.0
            + age_score * 0.5
            + rotation * 1.25
        )
