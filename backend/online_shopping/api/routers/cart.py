from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db
from online_shopping.api.schemas import CartItemCreate, CartItemUpdate, CartItemOut, ShoppingCartOut, ProductOut, CategoryOut
from online_shopping.models.product import Product

router = APIRouter()

# In-memory cart storage (per-process, not per-user — will be replaced with DB/Redis once auth is in place)
_cart_items: list[CartItemOut] = []


def _product_to_short_out(product: Product) -> ProductOut:
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


def _build_cart_response() -> ShoppingCartOut:
    subtotal = sum(item.price * item.quantity for item in _cart_items)
    total_quantity = sum(item.quantity for item in _cart_items)
    return ShoppingCartOut(items=list(_cart_items), total_quantity=total_quantity, subtotal=round(subtotal, 2))


@router.get("", response_model=ShoppingCartOut)
async def get_cart() -> ShoppingCartOut:
    return _build_cart_response()


@router.post("/items", response_model=ShoppingCartOut, status_code=status.HTTP_201_CREATED)
async def add_item(payload: CartItemCreate, db: AsyncSession = Depends(get_db)) -> ShoppingCartOut:
    result = await db.execute(
        select(Product).where(Product.name.ilike(payload.product_name))
    )
    product = result.scalars().first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    existing = next(
        (item for item in _cart_items if item.product.name.casefold() == product.name.casefold()),
        None,
    )
    if existing:
        existing.quantity += payload.quantity
    else:
        _cart_items.append(CartItemOut(
            quantity=payload.quantity,
            price=float(product.price),
            product=_product_to_short_out(product),
        ))
    return _build_cart_response()


@router.patch("/items/{product_name}", response_model=ShoppingCartOut)
async def update_item(product_name: str, payload: CartItemUpdate) -> ShoppingCartOut:
    item = next(
        (i for i in _cart_items if i.product.name.casefold() == product_name.casefold()),
        None,
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
    item.quantity = payload.quantity
    return _build_cart_response()


@router.delete("/items/{product_name}", response_model=ShoppingCartOut)
async def remove_item(product_name: str) -> ShoppingCartOut:
    before = len(_cart_items)
    _cart_items[:] = [
        item for item in _cart_items
        if item.product.name.casefold() != product_name.casefold()
    ]
    if len(_cart_items) == before:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
    return _build_cart_response()
