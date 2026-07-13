"""
Recommendations API — reads pre-computed results from PostgreSQL tables.

Endpoints:
  GET /recommendations/home                    — trending + popular
  GET /recommendations/cart                    — cart-appropriate recs (excludes cart items)
  GET /recommendations/products/{id}/similar   — similar products
  GET /recommendations/users/{username}        — personalized for a user

Filtering rules (applied to ALL endpoints):
  - product.status = 'active'
  - product.available_item_count > 0
  - No duplicate product_ids in results
  - cart scene: excludes products already in the user's cart
  - product_detail scene: excludes the seed product itself
  - Falls back to popular_products when specific recs run short
"""

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db, get_optional_user
from online_shopping.api.mappers import product_to_out
from online_shopping.models.account import Account
from online_shopping.models.product import Product
from online_shopping.models.recommendation_result import (
    ItemSimilarity,
    PopularProduct,
    RecommendationResult,
)

router = APIRouter()

MAX_RESULTS = 12
MIN_RESULTS = 4


def _cart_id_from_header(x_cart_id: str | None = Header(None)) -> str | None:
    return x_cart_id


# ── Shared helpers ────────────────────────────────────────────────

async def _load_active_products(db: AsyncSession, product_ids: list[str]) -> list[Product]:
    """Load active, in-stock products by ID list."""
    if not product_ids:
        return []
    import uuid as _uuid
    from sqlalchemy.orm import selectinload

    ordered_uids = []
    seen_uids = set()
    for pid in product_ids:
        try:
            uid = _uuid.UUID(pid)
        except (ValueError, TypeError):
            continue
        if uid not in seen_uids:
            seen_uids.add(uid)
            ordered_uids.append(uid)

    if not ordered_uids:
        return []

    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.variants),
        )
        .where(
            Product.id.in_(ordered_uids),
            Product.status == "active",
            Product.available_item_count > 0,
        )
        .limit(MAX_RESULTS * 2)
    )
    products_by_id = {product.id: product for product in result.scalars().all()}
    return [products_by_id[uid] for uid in ordered_uids if uid in products_by_id]


async def _get_cart_product_ids(db: AsyncSession, cart_id: str | None) -> set[str]:
    """Get product IDs in the user's cart for exclusion."""
    if not cart_id:
        return set()
    import uuid as _uuid
    try:
        cid = _uuid.UUID(cart_id)
    except (ValueError, TypeError):
        return set()

    from online_shopping.models.cart import CartItem
    from online_shopping.models.product_variant import ProductVariant

    variant_result = await db.execute(
        select(CartItem.product_variant_id).where(CartItem.cart_id == cid)
    )
    variant_ids = [row[0] for row in variant_result]
    if not variant_ids:
        return set()

    pv_result = await db.execute(
        select(ProductVariant.product_id).where(ProductVariant.id.in_(variant_ids))
    )
    return {str(row[0]) for row in pv_result}


async def _fallback_popular(db: AsyncSession, limit: int) -> list[Product]:
    """Fallback to popular products ranked by score."""
    result = await db.execute(
        select(PopularProduct.product_id)
        .order_by(PopularProduct.score.desc())
        .limit(limit * 2)
    )
    pids = [str(r[0]) for r in result]
    return await _load_active_products(db, pids)


def _build_response(scene: str, products: list[Product], meta: list[dict]) -> dict:
    """Format the API response."""
    items = []
    seen = set()
    meta_by_product_id = {
        str(m["product_id"]): m
        for m in meta
        if m.get("product_id")
    }
    for i, product in enumerate(products):
        pid = str(product.id)
        if pid in seen:
            continue
        seen.add(pid)
        m = meta_by_product_id.get(pid) or (meta[i] if i < len(meta) else {})
        items.append({
            "product": product_to_out(product).model_dump(),
            "score": m.get("score"),
            "reason": m.get("reason", "Recommended for you"),
            "algorithm": m.get("algorithm", "popular_v1"),
        })
        if len(items) >= MAX_RESULTS:
            break

    return {"scene": scene, "count": len(items), "items": items}


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/home")
async def recommendations_home(
    db: AsyncSession = Depends(get_db),
    current_user: Account | None = Depends(get_optional_user),
) -> dict:
    """Home page recommendations — trending + popular products."""
    # Try popular_products table first
    result = await db.execute(
        select(PopularProduct.product_id, PopularProduct.score, PopularProduct.rank)
        .order_by(PopularProduct.score.desc())
        .limit(MAX_RESULTS * 2)
    )
    rows = list(result)
    pids = [str(r[0]) for r in rows]
    meta = [{"product_id": str(r[0]), "score": r[1], "reason": f"#{r[2]} Trending", "algorithm": "popular_v1"} for r in rows]

    products = await _load_active_products(db, pids)

    # Fallback to rule-based if table is empty
    if not products:
        products = await _fallback_popular(db, MAX_RESULTS)
        meta = [{"product_id": str(product.id), "score": None, "reason": "You might like", "algorithm": "fallback"} for product in products]

    return _build_response("home", products, meta)


@router.get("/cart")
async def recommendations_cart(
    db: AsyncSession = Depends(get_db),
    current_user: Account | None = Depends(get_optional_user),
    cart_id: str | None = Depends(_cart_id_from_header),
) -> dict:
    """Cart page recommendations — excludes products already in cart."""
    excluded = await _get_cart_product_ids(db, cart_id)

    # Get popular, exclude cart items
    result = await db.execute(
        select(PopularProduct.product_id, PopularProduct.score, PopularProduct.rank)
        .order_by(PopularProduct.score.desc())
        .limit(MAX_RESULTS * 2 + len(excluded))
    )
    rows = [(str(r[0]), r[1], r[2]) for r in result if str(r[0]) not in excluded]

    pids = [r[0] for r in rows[:MAX_RESULTS * 2]]
    meta = [{"product_id": r[0], "score": r[1], "reason": f"Popular #{r[2]}", "algorithm": "popular_v1"} for r in rows[:MAX_RESULTS * 2]]

    products = await _load_active_products(db, pids)
    return _build_response("cart", products, meta)


@router.get("/products/{product_id}/similar")
async def recommendations_similar(
    product_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Similar products — based on item_similarities table."""
    import uuid as _uuid

    try:
        pid_uuid = _uuid.UUID(product_id)
    except (ValueError, TypeError):
        # Try lookup by name
        name_result = await db.execute(
            select(Product.id).where(
                Product.name.ilike(product_id),
                Product.status == "active",
            )
        )
        row = name_result.scalars().first()
        if row:
            pid_uuid = row
        else:
            return {"scene": "product_detail", "count": 0, "items": []}

    # Get similar products, excluding self
    result = await db.execute(
        select(ItemSimilarity.similar_product_id, ItemSimilarity.score, ItemSimilarity.reason)
        .where(
            ItemSimilarity.product_id == pid_uuid,
            ItemSimilarity.similar_product_id != pid_uuid,
        )
        .order_by(ItemSimilarity.score.desc())
        .limit(MAX_RESULTS * 2)
    )
    rows = list(result)
    pids = [str(r[0]) for r in rows]
    meta = [{"product_id": str(r[0]), "score": r[1], "reason": r[2] or "Similar product", "algorithm": "itemcf_v1"} for r in rows]

    products = await _load_active_products(db, pids)

    # Fallback to popular if no similar items
    if not products:
        popular_result = await db.execute(
            select(PopularProduct.product_id, PopularProduct.score, PopularProduct.rank)
            .where(PopularProduct.product_id != pid_uuid)
            .order_by(PopularProduct.score.desc())
            .limit(MAX_RESULTS * 2)
        )
        pop_rows = list(popular_result)
        pids = [str(r[0]) for r in pop_rows]
        meta = [{"product_id": str(r[0]), "score": r[1], "reason": "Popular product", "algorithm": "popular_v1"} for r in pop_rows]
        products = await _load_active_products(db, pids)

    return _build_response("product_detail", products, meta)


@router.get("/users/{username}")
async def recommendations_for_user(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Personalized recommendations for a specific user (by username or anonymous_id)."""
    # Try user_key match
    result = await db.execute(
        select(
            RecommendationResult.product_id,
            RecommendationResult.score,
            RecommendationResult.reason,
            RecommendationResult.algorithm,
        )
        .where(
            RecommendationResult.user_key == username,
            RecommendationResult.scene == "home",
        )
        .order_by(RecommendationResult.score.desc())
        .limit(MAX_RESULTS * 2)
    )
    rows = list(result)

    if rows:
        pids = [str(r[0]) for r in rows]
        meta = [{"product_id": str(r[0]), "score": r[1], "reason": r[2] or "For you", "algorithm": r[3]} for r in rows]
    else:
        # Fallback to popular
        pop_result = await db.execute(
            select(PopularProduct.product_id, PopularProduct.score, PopularProduct.rank)
            .order_by(PopularProduct.score.desc())
            .limit(MAX_RESULTS * 2)
        )
        pop_rows = list(pop_result)
        pids = [str(r[0]) for r in pop_rows]
        meta = [{"product_id": str(r[0]), "score": r[1], "reason": "Trending now", "algorithm": "popular_v1"} for r in pop_rows]

    products = await _load_active_products(db, pids)
    return _build_response("account", products, meta)
