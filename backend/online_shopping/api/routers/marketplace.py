from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db
from online_shopping.repositories.catalog_repository import CatalogRepository
from online_shopping.repositories.marketplace_repository import MarketplaceRepository
from online_shopping.services.marketplace_service import MarketplaceService

router = APIRouter()


@router.get("/hall")
async def get_hall(db: AsyncSession = Depends(get_db)) -> dict:
    """Return marketplace metadata: shops, categories, and capped shop sections.

    The full product catalog is no longer included. The frontend fetches
    paginated product batches via GET /hall/products.
    """
    service = MarketplaceService(
        catalog_repository=CatalogRepository(db),
        marketplace_repository=MarketplaceRepository(db),
    )
    return await service.hall_payload()


@router.get("/hall/products")
async def get_hall_products(
    q: str | None = Query(None, description="Search query"),
    shop: str | None = Query(None, description="Filter by shop slug"),
    category: str | None = Query(None, description="Filter by category slug"),
    limit: int = Query(24, ge=1, le=60, description="Products per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return a paginated page of marketplace products with shop metadata.

    Supports optional filtering by search query, shop slug, and category slug.
    Default page size is 24, capped at 60.
    """
    service = MarketplaceService(
        catalog_repository=CatalogRepository(db),
        marketplace_repository=MarketplaceRepository(db),
    )
    return await service.hall_products_paginated(
        q=q,
        shop=shop,
        category=category,
        limit=limit,
        offset=offset,
    )
