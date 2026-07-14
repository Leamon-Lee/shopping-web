from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_current_user, get_db, get_optional_user
from online_shopping.api.mappers import cart_to_out
from online_shopping.api.schemas import (
    CartAddressPayload,
    CartEmailPayload,
    CartItemCreate,
    CartItemUpdate,
    CartPaymentSessionPayload,
    CartShippingMethodPayload,
    ShoppingCartOut,
)
from online_shopping.models.account import Account
from online_shopping.services.cart_service import CartService

router = APIRouter()


def _cart_id_from_header(x_cart_id: str | None = Header(None)) -> str | None:
    """Extract cart_id from X-Cart-Id header for guest cart isolation."""
    return x_cart_id


def _cart_owner_from_header(x_cart_owner: str | None = Header(None)) -> str | None:
    """Extract route owner from X-Cart-Owner for username cart routes."""
    return x_cart_owner


async def _cart_email_for_request(
    db: AsyncSession,
    current_user: Account | None,
    cart_owner: str | None,
) -> str | None:
    if current_user:
        return current_user.email
    if not cart_owner or cart_owner == "guest":
        return None

    result = await db.execute(
        select(Account.email).where(
            or_(Account.email == cart_owner, Account.user_name == cart_owner)
        )
    )
    return result.scalars().first()


@router.get("", response_model=ShoppingCartOut)
async def get_cart(
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    cart_id: str | None = Depends(_cart_id_from_header),
    cart_owner: str | None = Depends(_cart_owner_from_header),
) -> ShoppingCartOut:
    """Get the current user's cart or a guest cart identified by X-Cart-Id."""
    email = await _cart_email_for_request(db, current_user, cart_owner)
    cart = await CartService(db).get_cart(
        email=email,
        cart_id=cart_id,
    )
    return cart_to_out(cart)


@router.post("/items", response_model=ShoppingCartOut, status_code=status.HTTP_201_CREATED)
async def add_item(
    payload: CartItemCreate,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    cart_id: str | None = Depends(_cart_id_from_header),
    cart_owner: str | None = Depends(_cart_owner_from_header),
) -> ShoppingCartOut:
    """Add an item to the cart."""
    email = await _cart_email_for_request(db, current_user, cart_owner)
    cart = await CartService(db).add_item(
        payload.product_name,
        payload.quantity,
        email=email,
        cart_id=cart_id,
    )
    return cart_to_out(cart)


@router.patch("/items/{item_identity}", response_model=ShoppingCartOut)
async def update_item(
    item_identity: str,
    payload: CartItemUpdate,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    cart_id: str | None = Depends(_cart_id_from_header),
    cart_owner: str | None = Depends(_cart_owner_from_header),
) -> ShoppingCartOut:
    """Update quantity of a cart item."""
    email = await _cart_email_for_request(db, current_user, cart_owner)
    cart = await CartService(db).update_item(
        item_identity,
        payload.quantity,
        email=email,
        cart_id=cart_id,
    )
    return cart_to_out(cart)


@router.delete("/items/{item_identity}", response_model=ShoppingCartOut)
async def remove_item(
    item_identity: str,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    cart_id: str | None = Depends(_cart_id_from_header),
    cart_owner: str | None = Depends(_cart_owner_from_header),
) -> ShoppingCartOut:
    """Remove an item from the cart."""
    email = await _cart_email_for_request(db, current_user, cart_owner)
    cart = await CartService(db).remove_item(
        item_identity,
        email=email,
        cart_id=cart_id,
    )
    return cart_to_out(cart)


# ── Checkout endpoints ──────────────────────────────────────────────


@router.patch("/addresses", response_model=ShoppingCartOut)
async def set_cart_addresses(
    payload: CartAddressPayload,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    cart_id: str | None = Depends(_cart_id_from_header),
    cart_owner: str | None = Depends(_cart_owner_from_header),
) -> ShoppingCartOut:
    """Set shipping and billing addresses on the cart. Also sets email."""
    shipping = payload.model_dump()
    # Use the email from the address form, falling back to authenticated user's email
    form_email = (shipping.get("email") or "").strip()
    owner_email = await _cart_email_for_request(db, current_user, cart_owner)
    effective_email = form_email or owner_email
    cart = await CartService(db).set_addresses(
        shipping_address=shipping,
        billing_address=shipping,  # billing same as shipping by default
        email=effective_email,
        cart_id=cart_id,
    )
    return cart_to_out(cart)


@router.patch("/email", response_model=ShoppingCartOut)
async def set_cart_email(
    payload: CartEmailPayload,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    cart_id: str | None = Depends(_cart_id_from_header),
    cart_owner: str | None = Depends(_cart_owner_from_header),
) -> ShoppingCartOut:
    """Set email on the cart."""
    existing_email = await _cart_email_for_request(db, current_user, cart_owner)
    cart = await CartService(db).set_email(
        payload.email,
        existing_email=existing_email,
        cart_id=cart_id,
    )
    return cart_to_out(cart)


@router.get("/shipping-options")
async def list_shipping_options() -> list[dict]:
    """Return available shipping options (demo)."""
    return [
        {
            "id": "backend_standard_shipping",
            "name": "Standard Shipping",
            "price_type": "flat",
            "amount": 0,
            "data": {},
            "service_zone": {"fulfillment_set": {"type": "shipping"}},
        },
        {
            "id": "backend_express_shipping",
            "name": "Express Shipping",
            "price_type": "flat",
            "amount": 15.0,
            "data": {},
            "service_zone": {"fulfillment_set": {"type": "shipping"}},
        },
    ]


@router.patch("/shipping-method", response_model=ShoppingCartOut)
async def set_shipping_method(
    payload: CartShippingMethodPayload,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    cart_id: str | None = Depends(_cart_id_from_header),
    cart_owner: str | None = Depends(_cart_owner_from_header),
) -> ShoppingCartOut:
    """Set the shipping method for the cart."""
    email = await _cart_email_for_request(db, current_user, cart_owner)
    cart = await CartService(db).set_shipping_method(
        payload.shipping_method_id,
        email=email,
        cart_id=cart_id,
    )
    return cart_to_out(cart)


@router.post("/payment-session", response_model=ShoppingCartOut)
async def create_payment_session(
    payload: CartPaymentSessionPayload | None = None,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    cart_id: str | None = Depends(_cart_id_from_header),
    cart_owner: str | None = Depends(_cart_owner_from_header),
) -> ShoppingCartOut:
    """Create a demo payment session for the cart."""
    provider_id = payload.provider_id if payload else "pp_system_default"
    email = await _cart_email_for_request(db, current_user, cart_owner)
    cart = await CartService(db).create_payment_session(
        provider_id=provider_id,
        email=email,
        cart_id=cart_id,
    )
    return cart_to_out(cart)
