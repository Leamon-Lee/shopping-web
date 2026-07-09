from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
import bcrypt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.api.deps import get_db
from online_shopping.api.schemas import (
    AccountOut,
    AddressOut,
    AddressCreate,
    AddressUpdate,
    LoginPayload,
    RegisterPayload,
    NameOut,
    PhoneOut,
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
            street_address=primary_address.street if primary_address else "",
            city=primary_address.city if primary_address else "",
            state=primary_address.state if primary_address else "",
            zip_code=primary_address.postal_code if primary_address else "",
            country=primary_address.country if primary_address else "",
        ),
        email=account.email,
        phone=PhoneOut(
            country_code=account.phone_country_code or "",
            number=account.phone_number or "",
        ),
    )


def _address_to_out(address: Address) -> AddressOut:
    return AddressOut(
        street_address=address.street,
        city=address.city,
        state=address.state,
        zip_code=address.postal_code,
        country=address.country,
    )


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


@router.post("/login", response_model=AccountOut)
async def login_endpoint(payload: LoginPayload, db: AsyncSession = Depends(get_db)) -> AccountOut:
    result = await db.execute(
        select(Account).options(selectinload(Account.addresses)).where(
            (Account.user_name == payload.email) | (Account.email == payload.email)
        )
    )
    account = result.scalars().first()
    if account is None or not bcrypt.checkpw(payload.password.encode(), account.password_hash.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    result = await db.execute(
        select(Account).options(selectinload(Account.addresses)).where(Account.id == account.id)
    )
    account = result.scalars().one()

    return _account_to_out(account)


@router.get("/me", response_model=AccountOut)
async def get_me(email: str, db: AsyncSession = Depends(get_db)) -> AccountOut:
    result = await db.execute(
        select(Account).options(selectinload(Account.addresses)).where(Account.email == email)
    )
    account = result.scalars().first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return _account_to_out(account)


@router.put("/me", response_model=AccountOut)
async def update_me(
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
    phone_country_code: str | None = None,
    phone_number: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> AccountOut:
    result = await db.execute(select(Account).options(selectinload(Account.addresses)).where(Account.email == email))
    account = result.scalars().first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    if first_name is not None:
        account.first_name = first_name
    if last_name is not None:
        account.last_name = last_name
    if phone_country_code is not None:
        account.phone_country_code = phone_country_code
    if phone_number is not None:
        account.phone_number = phone_number

    await db.commit()
    await db.refresh(account)
    return _account_to_out(account)


@router.get("/me/addresses", response_model=list[AddressOut])
async def list_addresses(email: str, db: AsyncSession = Depends(get_db)) -> list[AddressOut]:
    result = await db.execute(select(Account).options(selectinload(Account.addresses)).where(Account.email == email))
    account = result.scalars().first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return [_address_to_out(a) for a in account.addresses]


@router.post("/me/addresses", response_model=list[AddressOut], status_code=status.HTTP_201_CREATED)
async def add_address(
    email: str,
    payload: AddressCreate,
    db: AsyncSession = Depends(get_db),
) -> list[AddressOut]:
    result = await db.execute(select(Account).options(selectinload(Account.addresses)).where(Account.email == email))
    account = result.scalars().first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    address = Address(
        account_id=account.id,
        street=payload.street,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        country=payload.country,
        is_default_shipping=payload.is_default_shipping,
    )
    db.add(address)
    await db.commit()
    await db.refresh(account)
    return [_address_to_out(a) for a in account.addresses]


@router.put("/me/addresses/{address_id}", response_model=list[AddressOut])
async def update_address(
    email: str,
    address_id: str,
    payload: AddressUpdate,
    db: AsyncSession = Depends(get_db),
) -> list[AddressOut]:
    result = await db.execute(select(Account).options(selectinload(Account.addresses)).where(Account.email == email))
    account = result.scalars().first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    address = next((a for a in account.addresses if str(a.id) == address_id), None)
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
    await db.refresh(account)
    return [_address_to_out(a) for a in account.addresses]


@router.delete("/me/addresses/{address_id}", response_model=list[AddressOut])
async def delete_address(
    email: str,
    address_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[AddressOut]:
    result = await db.execute(select(Account).options(selectinload(Account.addresses)).where(Account.email == email))
    account = result.scalars().first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    address = next((a for a in account.addresses if str(a.id) == address_id), None)
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")

    await db.delete(address)
    await db.commit()
    await db.refresh(account)
    return [_address_to_out(a) for a in account.addresses]
