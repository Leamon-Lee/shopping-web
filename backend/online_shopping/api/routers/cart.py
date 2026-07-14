from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_current_user, get_db, get_optional_user
from online_shopping.api.behavior_events import record_behavior_event
from online_shopping.api.mappers import cart_to_out
from online_shopping.api.schemas import CartItemCreate, CartItemUpdate, ShoppingCartOut
from online_shopping.models.account import Account
from online_shopping.services.cart_service import CartService

router = APIRouter()


@router.get("", response_model=ShoppingCartOut)
async def get_cart(
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ShoppingCartOut:
    """Get the current user's cart or the default guest cart."""
    cart = await CartService(db).get_cart(email=current_user.email if current_user else None)
    return cart_to_out(cart)


@router.post("/items", response_model=ShoppingCartOut, status_code=status.HTTP_201_CREATED)
async def add_item(
    payload: CartItemCreate,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ShoppingCartOut:
    """Add an item to the cart."""
    cart = await CartService(db).add_item(
        payload.product_name,
        payload.quantity,
        email=current_user.email if current_user else None,
    )
    await record_behavior_event(
        db,
        "add_to_cart",
        current_user,
        product_identity=payload.product_name,
        quantity=payload.quantity,
        source_page="/cart",
        metadata={"source": "cart_api"},
    )
    await db.commit()
    return cart_to_out(cart)


@router.patch("/items/{item_identity}", response_model=ShoppingCartOut)
async def update_item(
    item_identity: str,
    payload: CartItemUpdate,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ShoppingCartOut:
    """Update quantity of a cart item."""
    cart = await CartService(db).update_item(
        item_identity,
        payload.quantity,
        email=current_user.email if current_user else None,
    )
    return cart_to_out(cart)


@router.delete("/items/{item_identity}", response_model=ShoppingCartOut)
async def remove_item(
    item_identity: str,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ShoppingCartOut:
    """Remove an item from the cart."""
    await record_behavior_event(
        db,
        "remove_from_cart",
        current_user,
        product_identity=item_identity,
        source_page="/cart",
        metadata={"source": "cart_api"},
    )
    cart = await CartService(db).remove_item(
        item_identity,
        email=current_user.email if current_user else None,
    )
    await db.commit()
    return cart_to_out(cart)
