from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
import bcrypt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.api.auth.jwt import create_access_token
from online_shopping.api.deps import get_current_user, get_db
from online_shopping.api.schemas import (
    AccountOut,
    AccountUpdate,
    AddressOut,
    AddressCreate,
    AddressUpdate,
    LoginPayload,
    RegisterPayload,
    NameOut,
    PhoneOut,
    TokenResponse,
)
from online_shopping.models.account import Account
from online_shopping.models.address import Address
from online_shopping.domain.enums.account_status import AccountStatus

router = APIRouter()


def _account_to_out(account: Account) -> AccountOut:
    primary_address = next((a for a in account.addresses if a.is_default_shipping), None)
    if primary_address is None and account.addresses:
        primary_address = account.addresses[0]

    return AccountOut(
        user_name=account.user_name,
        status=AccountStatus(account.status),
        name=NameOut(first_name=account.first_name, last_name=account.last_name),
        shipping_address=AddressOut(
            street=primary_address.street if primary_address else "",
            city=primary_address.city if primary_address else "",
            state=primary_address.state if primary_address else "",
            postal_code=primary_address.postal_code if primary_address else "",
            country=primary_address.country if primary_address else "",
        ),
        email=account.email,
        phone=PhoneOut(
            country_code=account.phone_country_code or "",
            number=account.phone_number or "",
        ),
        addresses=[_address_to_out(a) for a in account.addresses],
    )


def _address_to_out(address: Address) -> AddressOut:
    return AddressOut(
        street=address.street,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        country=address.country,
    )


# ── Public endpoints ──────────────────────────────────────────────


@router.post("/register", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterPayload, db: AsyncSession = Depends(get_db)) -> AccountOut:
    existing = await db.execute(
        select(Account).options(selectinload(Account.addresses)).where(
            (Account.user_name == payload.email) | (Account.email == payload.email)
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists.")

    account = Account(
        user_name=payload.email,
        password_hash=bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode(),
        status=AccountStatus.ACTIVE.value,
        first_name=payload.first_name or "",
        last_name=payload.last_name or "",
        email=payload.email,
        phone_country_code=payload.phone_country_code or "",
        phone_number=payload.phone_number or "",
    )
    db.add(account)
    await db.flush()

    if payload.street:
        addr = Address(
            account_id=account.id,
            street=payload.street,
            city=payload.city or "",
            state=payload.state or "",
            postal_code=payload.postal_code or "",
            country=payload.country or "",
            is_default_shipping=True,
        )
        db.add(addr)

    await db.commit()
    await db.refresh(account)

    result = await db.execute(
        select(Account).options(selectinload(Account.addresses)).where(Account.id == account.id)
    )
    account = result.scalars().one()

    return _account_to_out(account)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginPayload, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate user and return a JWT access token."""
    result = await db.execute(
        select(Account).options(selectinload(Account.addresses)).where(
            (Account.user_name == payload.email) | (Account.email == payload.email)
        )
    )
    account = result.scalars().first()
    if account is None or not bcrypt.checkpw(payload.password.encode(), account.password_hash.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    # Refresh to ensure relationships are loaded
    result = await db.execute(
        select(Account).options(selectinload(Account.addresses)).where(Account.id == account.id)
    )
    account = result.scalars().one()

    token = create_access_token(data={"sub": account.email, "role": account.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_account_to_out(account),
    )


# ── Protected endpoints (require JWT) ─────────────────────────────


@router.get("/me", response_model=AccountOut)
async def get_me(
    current_user: Account = Depends(get_current_user),
) -> AccountOut:
    """Return the currently authenticated user's profile."""
    return _account_to_out(current_user)


@router.put("/me", response_model=AccountOut)
async def update_me(
    payload: AccountUpdate,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccountOut:
    """Update the currently authenticated user's profile fields."""
    if payload.first_name is not None:
        current_user.first_name = payload.first_name
    if payload.last_name is not None:
        current_user.last_name = payload.last_name
    if payload.phone_country_code is not None:
        current_user.phone_country_code = payload.phone_country_code
    if payload.phone_number is not None:
        current_user.phone_number = payload.phone_number

    await db.commit()
    await db.refresh(current_user)
    return _account_to_out(current_user)


# ── Address endpoints (protected) ──────────────────────────────────


@router.get("/me/addresses", response_model=list[AddressOut])
async def list_addresses(
    current_user: Account = Depends(get_current_user),
) -> list[AddressOut]:
    """List addresses for the currently authenticated user."""
    return [_address_to_out(a) for a in current_user.addresses]


@router.post("/me/addresses", response_model=list[AddressOut], status_code=status.HTTP_201_CREATED)
async def add_address(
    payload: AddressCreate,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AddressOut]:
    """Add a new address for the currently authenticated user."""
    address = Address(
        account_id=current_user.id,
        street=payload.street,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        country=payload.country,
        is_default_shipping=payload.is_default_shipping,
    )
    db.add(address)
    await db.commit()
    await db.refresh(current_user)
    return [_address_to_out(a) for a in current_user.addresses]


@router.put("/me/addresses/{address_id}", response_model=list[AddressOut])
async def update_address(
    address_id: str,
    payload: AddressUpdate,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AddressOut]:
    """Update an address for the currently authenticated user."""
    address = next((a for a in current_user.addresses if str(a.id) == address_id), None)
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")

    if payload.street is not None:
        address.street = payload.street
    if payload.city is not None:
        address.city = payload.city
    if payload.state is not None:
        address.state = payload.state
    if payload.postal_code is not None:
        address.postal_code = payload.postal_code
    if payload.country is not None:
        address.country = payload.country
    if payload.is_default_shipping is not None:
        address.is_default_shipping = payload.is_default_shipping

    await db.commit()
    await db.refresh(current_user)
    return [_address_to_out(a) for a in current_user.addresses]


@router.delete("/me/addresses/{address_id}", response_model=list[AddressOut])
async def delete_address(
    address_id: str,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AddressOut]:
    """Delete an address for the currently authenticated user."""
    address = next((a for a in current_user.addresses if str(a.id) == address_id), None)
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")

    await db.delete(address)
    await db.commit()
    await db.refresh(current_user)
    return [_address_to_out(a) for a in current_user.addresses]


# ── Wishlist endpoints (protected) ──────────────────────────────────


@router.get("/me/wishlist")
async def list_wishlist(
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List wishlist items for the current user."""
    from online_shopping.models.wishlist import WishlistItem
    from sqlalchemy.orm import selectinload
    from online_shopping.models.product import Product

    result = await db.execute(
        select(WishlistItem)
        .options(selectinload(WishlistItem.product))
        .where(WishlistItem.account_id == current_user.id)
        .order_by(WishlistItem.created_at.desc())
    )
    items = list(result.scalars().all())
    return {
        "items": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "product_name": item.product.name if item.product else "",
            }
            for item in items
        ]
    }


@router.post("/me/wishlist/items", status_code=status.HTTP_201_CREATED)
async def add_wishlist_item(
    product_id: str,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a product to wishlist."""
    from online_shopping.models.wishlist import WishlistItem
    import uuid as _uuid

    item = WishlistItem(
        account_id=current_user.id,
        product_id=_uuid.UUID(product_id),
    )
    db.add(item)
    await db.commit()
    return {"id": str(item.id), "product_id": str(item.product_id)}


@router.delete("/me/wishlist/items/{product_id}")
async def remove_wishlist_item(
    product_id: str,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove a product from wishlist."""
    from online_shopping.models.wishlist import WishlistItem
    import uuid as _uuid

    result = await db.execute(
        select(WishlistItem).where(
            WishlistItem.account_id == current_user.id,
            WishlistItem.product_id == _uuid.UUID(product_id),
        )
    )
    item = result.scalars().first()
    if item:
        await db.delete(item)
        await db.commit()
    return {"removed": True}


# ── Review endpoints ────────────────────────────────────────────────


@router.get("/me/reviews")
async def list_my_reviews(
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List reviews written by the current user."""
    from online_shopping.models.review import Review

    result = await db.execute(
        select(Review)
        .where(Review.account_id == current_user.id)
        .order_by(Review.created_at.desc())
    )
    reviews = list(result.scalars().all())
    return {
        "reviews": [
            {
                "id": str(r.id),
                "product_id": str(r.product_id),
                "rating": r.rating,
                "title": r.title,
                "content": r.content,
            }
            for r in reviews
        ]
    }


@router.put("/me/reviews/{review_id}")
async def update_review(
    review_id: str,
    rating: int | None = None,
    title: str | None = None,
    content: str | None = None,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a review."""
    from online_shopping.models.review import Review
    import uuid as _uuid

    result = await db.execute(
        select(Review).where(
            Review.id == _uuid.UUID(review_id),
            Review.account_id == current_user.id,
        )
    )
    review = result.scalars().first()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")

    if rating is not None:
        review.rating = max(1, min(5, rating))
    if title is not None:
        review.title = title
    if content is not None:
        review.content = content

    await db.commit()
    return {"id": str(review.id), "rating": review.rating}


@router.delete("/me/reviews/{review_id}")
async def delete_review(
    review_id: str,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a review."""
    from online_shopping.models.review import Review
    import uuid as _uuid

    result = await db.execute(
        select(Review).where(
            Review.id == _uuid.UUID(review_id),
            Review.account_id == current_user.id,
        )
    )
    review = result.scalars().first()
    if review:
        await db.delete(review)
        await db.commit()
    return {"removed": True}
