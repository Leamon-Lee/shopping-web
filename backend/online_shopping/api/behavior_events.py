from __future__ import annotations

import uuid as _uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.models.account import Account
from online_shopping.models.product import Product
from online_shopping.models.product_variant import ProductVariant
from online_shopping.models.shop import Shop, ShopProduct
from online_shopping.models.user_behavior_event import UserBehaviorEvent


def _try_uuid(value: str | _uuid.UUID | None) -> _uuid.UUID | None:
    if isinstance(value, _uuid.UUID):
        return value
    if not value:
        return None
    try:
        return _uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


async def resolve_event_product(
    db: AsyncSession,
    identity: str | _uuid.UUID | None = None,
    product_id: str | _uuid.UUID | None = None,
) -> Product | None:
    lookup_id = _try_uuid(product_id or identity)
    if lookup_id:
        variant_result = await db.execute(
            select(ProductVariant)
            .options(selectinload(ProductVariant.product).selectinload(Product.category))
            .where(ProductVariant.id == lookup_id)
        )
        variant = variant_result.scalars().first()
        if variant is not None:
            return variant.product

        product_result = await db.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == lookup_id)
        )
        product = product_result.scalars().first()
        if product is not None:
            return product

    if not identity:
        return None

    folded = str(identity).casefold()
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(or_(Product.slug == folded, Product.name.ilike(str(identity))))
        .limit(1)
    )
    return result.scalars().first()


async def record_behavior_event(
    db: AsyncSession,
    event_type: str,
    current_user: Account | None = None,
    *,
    product: Product | None = None,
    product_identity: str | _uuid.UUID | None = None,
    product_id: str | _uuid.UUID | None = None,
    quantity: int | None = None,
    price: float | None = None,
    query: str | None = None,
    source_page: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> UserBehaviorEvent:
    product = product or await resolve_event_product(
        db,
        identity=product_identity,
        product_id=product_id,
    )

    shop_id = None
    shop_name = None
    if product is not None:
        shop_result = await db.execute(
            select(Shop.id, Shop.name)
            .join(ShopProduct, ShopProduct.shop_id == Shop.id)
            .where(ShopProduct.product_id == product.id)
            .limit(1)
        )
        shop_row = shop_result.first()
        if shop_row:
            shop_id = shop_row[0]
            shop_name = shop_row[1]

    event = UserBehaviorEvent(
        event_type=event_type,
        account_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else None,
        product_id=product.id if product is not None else _try_uuid(product_id),
        product_name=product.name if product is not None else None,
        product_slug=product.slug if product is not None else None,
        shop_id=shop_id,
        shop_name=shop_name,
        category_id=product.category_id if product is not None else None,
        category_name=product.category.name if product is not None and product.category else None,
        query=query,
        quantity=quantity,
        price=price if price is not None else float(product.price) if product is not None else None,
        source_page=source_page,
        metadata_json=metadata or {},
    )
    db.add(event)
    await db.flush()
    return event
