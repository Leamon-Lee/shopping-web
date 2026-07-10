from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class ShopSummary:
    id: UUID
    name: str
    product_count: int
    categories: tuple[str, ...]


class MarketplaceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_shop_summaries(self) -> list[ShopSummary]:
        result = await self.db.execute(
            text(
                """
                SELECT
                    s.id,
                    s.name,
                    count(DISTINCT p.id)::int AS product_count,
                    coalesce(
                        array_remove(array_agg(DISTINCT c.name ORDER BY c.name), NULL),
                        ARRAY[]::varchar[]
                    ) AS categories
                FROM shops s
                LEFT JOIN shop_products sp ON sp.shop_id = s.id
                LEFT JOIN products p ON p.id = sp.product_id
                LEFT JOIN product_categories c ON c.id = p.category_id
                WHERE s.status = 'active'
                GROUP BY s.id, s.name
                ORDER BY s.name
                """
            )
        )
        return [
            ShopSummary(
                id=row.id,
                name=row.name,
                product_count=row.product_count,
                categories=tuple(row.categories or []),
            )
            for row in result
        ]

    async def product_shop_map(self) -> dict[str, dict[str, str]]:
        result = await self.db.execute(
            text(
                """
                SELECT p.id AS product_id, s.id AS shop_id, s.name AS shop_name
                FROM products p
                JOIN shop_products sp ON sp.product_id = p.id
                JOIN shops s ON s.id = sp.shop_id
                WHERE s.status = 'active'
                """
            )
        )
        return {
            str(row.product_id): {
                "shop_id": str(row.shop_id),
                "shop_name": row.shop_name,
            }
            for row in result
        }
