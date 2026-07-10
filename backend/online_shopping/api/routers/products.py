"""Product & category endpoints — delegates to CatalogService."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_current_user, get_db, require_manager
from online_shopping.api.mappers import product_to_out
from online_shopping.api.schemas import CategoryOut, ProductCreate, ProductOut
from online_shopping.models.account import Account
from online_shopping.models.product_image import ProductImage
from online_shopping.repositories.catalog_repository import CatalogRepository
from online_shopping.services.catalog_service import CatalogService
from online_shopping.storage import get_image_url, upload_product_image

router = APIRouter()


# ── Public read endpoints ─────────────────────────────────────────


@router.get("", response_model=list[ProductOut])
async def list_products(
    shop: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[ProductOut]:
    """List all products, optionally filtered by shop slug, search query, with pagination."""
    service = CatalogService(db)
    products = await service.list_products(shop=shop)

    # Apply search filter (client-side for now; TODO: full-text search in DB)
    if q:
        query = q.strip().lower()
        products = [
            p for p in products
            if query in p.name.lower()
            or query in p.description.lower()
            or (p.category and query in p.category.name.lower())
        ]

    # Apply pagination
    total = len(products)
    products = products[offset : offset + limit]

    return [product_to_out(product) for product in products]


@router.get("/search", response_model=list[ProductOut])
async def search_products(
    q: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[ProductOut]:
    """Search products by name, description, or category."""
    service = CatalogService(db)
    products = await service.list_products()
    query = q.strip().lower()
    results = [
        p for p in products
        if query in p.name.lower()
        or query in p.description.lower()
        or (p.category and query in p.category.name.lower())
    ][:limit]
    return [product_to_out(product) for product in results]


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(
    db: AsyncSession = Depends(get_db),
) -> list[CategoryOut]:
    """List all product categories."""
    service = CatalogService(db)
    return await service.list_category_out()


@router.get("/{product_identity}", response_model=ProductOut)
async def get_product(
    product_identity: str,
    db: AsyncSession = Depends(get_db),
) -> ProductOut:
    """Get a single product by name, slug, or hash."""
    service = CatalogService(db)
    product = await service.find_product(product_identity)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product_to_out(product)


# ── Protected write endpoints ──────────────────────────────────────


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> ProductOut:
    """Create a new product. Requires manager or admin role."""
    service = CatalogService(db)
    product = await service.create_product(payload)
    return product_to_out(product)


@router.post("/{product_identity}/images", response_model=ProductOut)
async def upload_images(
    product_identity: str,
    files: list[UploadFile],
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> ProductOut:
    """Upload images for a product. Requires manager or admin role."""
    repo = CatalogRepository(db)
    product = await repo.find_product(product_identity)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    for idx, file in enumerate(files, start=len(product.images)):
        content = await file.read()
        upload_product_image(
            product.product_hash, file.filename, content,
            file.content_type or "image/jpeg",
        )
        image_url = get_image_url(product.product_hash, file.filename)
        await repo.save_image(ProductImage(
            product_id=product.id, image_url=image_url, rank=idx,
        ))

    await db.commit()
    updated = await repo.find_product(product_identity)
    assert updated is not None
    return product_to_out(updated)
