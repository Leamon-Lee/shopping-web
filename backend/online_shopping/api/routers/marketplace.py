from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db
from online_shopping.repositories.catalog_repository import CatalogRepository
from online_shopping.repositories.marketplace_repository import MarketplaceRepository
from online_shopping.services.marketplace_service import MarketplaceService

router = APIRouter()


@router.get("/hall")
async def get_hall(db: AsyncSession = Depends(get_db)) -> dict:
    service = MarketplaceService(
        catalog_repository=CatalogRepository(db),
        marketplace_repository=MarketplaceRepository(db),
    )
    return await service.hall_payload()
