from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db
from online_shopping.api.schemas import CategoryOut, ProductOut
from online_shopping.models.category import ProductCategory
from online_shopping.models.product import Product
from online_shopping.models.product_image import ProductImage
from online_shopping.services.hash_service import generate_product_hash
from online_shopping.storage import upload_product_image, get_image_url

router = APIRouter()


def _product_to_out(product: Product) -> ProductOut:
    category = product.category
    return ProductOut(
        name=product.name,
        description=product.description,
        price=float(product.price),
        available_item_count=product.available_item_count,
        category=CategoryOut(
            name=category.name if category else "",
            description=category.description if category else "",
        ),
    )


@router.get("", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)) -> list[ProductOut]:
    result = await db.execute(select(Product))
    return [_product_to_out(p) for p in result.scalars().all()]


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryOut]:
    result = await db.execute(select(ProductCategory))
    return [
        CategoryOut(name=c.name, description=c.description)
        for c in result.scalars().all()
    ]


@router.get("/{product_name}", response_model=ProductOut)
async def get_product(product_name: str, db: AsyncSession = Depends(get_db)) -> ProductOut:
    result = await db.execute(
        select(Product).where(Product.name.ilike(product_name))
    )
    product = result.scalars().first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return _product_to_out(product)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str,
    category_name: str,
    description: str = "",
    price: float = 0.01,
    available_item_count: int = 0,
    files: list[UploadFile] | None = None,
    db: AsyncSession = Depends(get_db),
) -> ProductOut:
    product_hash = generate_product_hash(name, category_name)

    existing = await db.execute(
        select(Product).where(Product.product_hash == product_hash)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product already exists.")

    # Find or create category
    cat_result = await db.execute(
        select(ProductCategory).where(ProductCategory.name == category_name)
    )
    category = cat_result.scalars().first()
    if category is None:
        category = ProductCategory(name=category_name, description="")
        db.add(category)
        await db.flush()

    import re
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "product"

    product = Product(
        product_hash=product_hash,
        category_id=category.id,
        name=name,
        slug=slug,
        description=description,
        price=price,
        available_item_count=available_item_count,
    )
    db.add(product)
    await db.flush()

    if files:
        for idx, file in enumerate(files):
            content = await file.read()
            upload_product_image(product_hash, file.filename, content, file.content_type or "image/jpeg")
            image_url = get_image_url(product_hash, file.filename)
            db.add(ProductImage(product_id=product.id, image_url=image_url, rank=idx))

    await db.commit()
    await db.refresh(product)

    return _product_to_out(product)
