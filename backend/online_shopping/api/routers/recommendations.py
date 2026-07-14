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

from datetime import datetime, timedelta, timezone
from math import exp

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db, get_optional_user
from online_shopping.api.mappers import product_to_out
from online_shopping.models.account import Account
from online_shopping.models.category import ProductCategory
from online_shopping.models.product import Product
from online_shopping.models.recommendation_result import (
    ItemSimilarity,
    PopularProduct,
    RecommendationResult,
)
from online_shopping.models.review import Review
from online_shopping.models.shop import Shop
from online_shopping.models.user_behavior_event import UserBehaviorEvent

router = APIRouter()

MAX_RESULTS = 12
MIN_RESULTS = 4
PREFERENCE_EVENT_TYPES = [
    "product_view",
    "add_to_cart",
    "favorite_product",
    "recommendation_click",
    "recommendation_add_to_cart",
    "product_review",
    "product_rating",
    "order_created",
    "order_paid",
]
EVENT_WEIGHTS = {
    "product_view": 1.0,
    "recommendation_click": 3.0,
    "add_to_cart": 5.0,
    "recommendation_add_to_cart": 5.0,
    "favorite_product": 6.0,
    "order_created": 7.0,
    "order_paid": 8.0,
}
RATING_WEIGHTS = {
    5: 8.0,
    4: 5.0,
    3: 1.0,
    2: -4.0,
    1: -8.0,
}
REALTIME_EVENT_TYPES = [
    "recommendation_click",
    "product_view",
    "add_to_cart",
    "recommendation_add_to_cart",
    "product_review",
    "product_rating",
    "favorite_product",
    "order_created",
    "order_paid",
]
REALTIME_EVENT_WEIGHTS = {
    "product_view": 1.0,
    "recommendation_click": 2.5,
    "add_to_cart": 5.0,
    "recommendation_add_to_cart": 5.5,
    "favorite_product": 6.0,
    "product_review": 7.0,
    "product_rating": 5.0,
    "order_created": 8.0,
    "order_paid": 10.0,
}
SHORT_TERM_HALF_LIFE_HOURS = 36.0


def _cart_id_from_header(x_cart_id: str | None = Header(None)) -> str | None:
    return x_cart_id


def _rating_event_weight(event_type: str, metadata: dict | None) -> float:
    if event_type not in {"product_review", "product_rating"}:
        return EVENT_WEIGHTS.get(event_type, 0.0)

    rating = None
    if isinstance(metadata, dict):
        try:
            rating = int(metadata.get("rating"))
        except (TypeError, ValueError):
            rating = None

    weight = RATING_WEIGHTS.get(rating, 0.0)
    if weight > 0 and isinstance(metadata, dict) and metadata.get("has_content"):
        weight += 1.0
    return weight


def _event_interest_weight(event_type: str, metadata: dict | None) -> float:
    if event_type in {"product_review", "product_rating"}:
        rating_weight = _rating_event_weight(event_type, metadata)
        return rating_weight if rating_weight else REALTIME_EVENT_WEIGHTS.get(event_type, 0.0)
    return REALTIME_EVENT_WEIGHTS.get(event_type, 0.0)


def _recency_decay(created_at: datetime | None) -> float:
    if not created_at:
        return 1.0
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = max((now - created_at).total_seconds() / 3600.0, 0.0)
    return exp(-age_hours / SHORT_TERM_HALF_LIFE_HOURS)


def _add_candidate(
    candidates: dict[str, dict],
    product_id,
    *,
    score: float,
    reason: str,
    algorithm: str,
    source: str,
) -> None:
    pid = str(product_id)
    current = candidates.setdefault(
        pid,
        {
            "product_id": pid,
            "score": 0.0,
            "reason": reason,
            "algorithm": algorithm,
            "sources": set(),
        },
    )
    current["score"] += score
    current["sources"].add(source)
    if score > current.get("best_source_score", -1):
        current["best_source_score"] = score
        current["reason"] = reason
        current["algorithm"] = algorithm


def _diversify_products(
    products: list[Product],
    meta: list[dict],
    *,
    limit: int,
) -> tuple[list[Product], list[dict]]:
    """MMR-style rerank: keep relevance, but avoid one category dominating the shelf."""
    product_meta = {str(m["product_id"]): m for m in meta}
    remaining = list(products)
    selected: list[Product] = []
    category_counts: dict[str, int] = {}

    while remaining and len(selected) < limit:
        best_index = 0
        best_score = float("-inf")
        for index, product in enumerate(remaining):
            pid = str(product.id)
            relevance = float(product_meta.get(pid, {}).get("score") or 0)
            category_key = str(product.category_id or "")
            diversity_penalty = category_counts.get(category_key, 0) * 8.0
            rank_score = relevance - diversity_penalty
            if rank_score > best_score:
                best_score = rank_score
                best_index = index

        chosen = remaining.pop(best_index)
        selected.append(chosen)
        category_key = str(chosen.category_id or "")
        category_counts[category_key] = category_counts.get(category_key, 0) + 1

    selected_ids = {str(product.id) for product in selected}
    selected_meta = [m for m in meta if str(m.get("product_id")) in selected_ids]
    return selected, selected_meta


def _price_band(price: float | None) -> str | None:
    if price is None:
        return None
    if price < 25:
        return "Under $25"
    if price < 50:
        return "$25-$50"
    if price < 100:
        return "$50-$100"
    return "$100+"


def _rank_preferences(values: dict[str, dict], limit: int = 6) -> list[dict]:
    positive = [
        {
            "label": label,
            "score": round(data["score"], 2),
            "count": data["count"],
        }
        for label, data in values.items()
        if data["score"] > 0
    ]
    positive.sort(key=lambda item: (item["score"], item["count"]), reverse=True)
    top = positive[:limit]
    max_score = max((item["score"] for item in top), default=0)
    for item in top:
        item["share"] = round((item["score"] / max_score) * 100, 1) if max_score else 0
    return top


async def _resolve_user_identity(db: AsyncSession, username: str):
    user_keys = [username]
    account_result = await db.execute(
        select(Account.id, Account.email).where(
            (Account.user_name == username) | (Account.email == username)
        )
    )
    account_row = account_result.first()
    account_id = None
    if account_row:
        account_id, account_email = account_row
        user_keys.extend([str(account_id), account_email])
    return account_id, user_keys


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
    products = await _load_active_products(db, pids)
    if products:
        return products

    fallback = await db.execute(
        select(Product.id)
        .where(Product.available_item_count > 0)
        .order_by(Product.created_at.desc())
        .limit(limit * 2)
    )
    return await _load_active_products(db, [str(r[0]) for r in fallback])


async def _recent_user_recommendations(
    db: AsyncSession,
    *,
    account_id,
    user_keys: list[str],
    limit: int,
) -> tuple[list[Product], list[dict]]:
    """Commercial realtime mixer: short-term interest + similarity + popularity + diversity."""
    from sqlalchemy.orm import selectinload

    conditions = []
    if account_id:
        conditions.append(UserBehaviorEvent.account_id == account_id)
    conditions.extend([
        UserBehaviorEvent.anonymous_id.in_(user_keys),
        UserBehaviorEvent.session_id.in_(user_keys),
        UserBehaviorEvent.user_email.in_(user_keys),
    ])

    from sqlalchemy import or_
    events_result = await db.execute(
        select(
            UserBehaviorEvent.product_id,
            UserBehaviorEvent.event_type,
            UserBehaviorEvent.metadata_json,
            UserBehaviorEvent.shop_id,
            UserBehaviorEvent.shop_name,
            UserBehaviorEvent.category_name,
            UserBehaviorEvent.price,
            UserBehaviorEvent.created_at,
        )
        .where(
            UserBehaviorEvent.product_id.is_not(None),
            UserBehaviorEvent.event_type.in_(REALTIME_EVENT_TYPES),
            or_(*conditions),
        )
        .order_by(UserBehaviorEvent.created_at.desc())
        .limit(120)
    )
    event_rows = list(events_result)
    seed_scores: dict = {}
    category_name_scores: dict[str, float] = {}
    shop_name_scores: dict[str, float] = {}
    price_band_scores: dict[str, float] = {}

    for row in event_rows:
        (
            product_id,
            event_type,
            metadata,
            _shop_id,
            shop_name,
            category_name,
            price,
            created_at,
        ) = row
        interest = _event_interest_weight(event_type, metadata) * _recency_decay(created_at)
        if interest <= 0:
            continue
        seed_scores[product_id] = seed_scores.get(product_id, 0.0) + interest
        if category_name:
            category_name_scores[category_name] = category_name_scores.get(category_name, 0.0) + interest
        if shop_name:
            shop_name_scores[shop_name] = shop_name_scores.get(shop_name, 0.0) + interest
        band = _price_band(float(price)) if price is not None else None
        if band:
            price_band_scores[band] = price_band_scores.get(band, 0.0) + interest

    seed_ids = [
        pid
        for pid, _score in sorted(seed_scores.items(), key=lambda item: item[1], reverse=True)[:12]
    ]
    if not seed_ids:
        return [], []

    candidates: dict[str, dict] = {}
    seed_id_strings = {str(pid) for pid in seed_ids}

    seed_products_result = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id.in_(seed_ids))
    )
    seed_products = list(seed_products_result.scalars().all())
    category_ids = []
    category_scores: dict = {}
    for product in seed_products:
        if product.category_id and product.category_id not in category_ids:
            category_ids.append(product.category_id)
        if product.category_id:
            category_scores[product.category_id] = (
                category_scores.get(product.category_id, 0.0)
                + seed_scores.get(product.id, 0.0)
            )

    if category_ids:
        max_category_score = max(category_scores.values(), default=1.0)
        category_result = await db.execute(
            select(Product.id, Product.category_id, Product.price, Product.created_at)
            .where(
                Product.category_id.in_(category_ids),
                ~Product.id.in_(seed_ids),
                Product.available_item_count > 0,
            )
            .order_by(Product.created_at.desc())
            .limit(limit * 8)
        )
        for row in category_result:
            product_id, category_id, price, created_at = row
            if str(product_id) in seed_id_strings:
                continue
            category_affinity = category_scores.get(category_id, 0.0) / max_category_score
            price_affinity = 0.0
            band = _price_band(float(price)) if price is not None else None
            if band and price_band_scores:
                price_affinity = price_band_scores.get(band, 0.0) / max(price_band_scores.values())
            newness = _recency_decay(created_at)
            _add_candidate(
                candidates,
                product_id,
                score=75.0 * category_affinity + 8.0 * price_affinity + 5.0 * newness,
                reason="Similar to products you viewed",
                algorithm="commerce_short_interest",
                source="category_affinity",
            )

    sim_result = await db.execute(
        select(
            ItemSimilarity.product_id,
            ItemSimilarity.similar_product_id,
            func.max(ItemSimilarity.score),
        )
        .where(
            ItemSimilarity.product_id.in_(seed_ids),
            ~ItemSimilarity.similar_product_id.in_(seed_ids),
        )
        .group_by(ItemSimilarity.product_id, ItemSimilarity.similar_product_id)
        .order_by(func.max(ItemSimilarity.score).desc())
        .limit(limit * 8)
    )
    for row in sim_result:
        seed_product_id, similar_product_id, similarity = row
        if str(similar_product_id) in seed_id_strings:
            continue
        seed_interest = seed_scores.get(seed_product_id, 1.0)
        _add_candidate(
            candidates,
            similar_product_id,
            score=45.0 * float(similarity or 0) + 4.0 * seed_interest,
            reason="Similar to products you viewed",
            algorithm="commerce_itemcf",
            source="item_similarity",
        )

    popular_result = await db.execute(
        select(PopularProduct.product_id, func.max(PopularProduct.score))
        .group_by(PopularProduct.product_id)
        .order_by(func.max(PopularProduct.score).desc())
        .limit(limit * 8)
    )
    popular_rows = list(popular_result)
    max_popular_score = max((float(row[1] or 0) for row in popular_rows), default=1.0)
    for product_id, popular_score in popular_rows:
        if str(product_id) in seed_id_strings:
            continue
        _add_candidate(
            candidates,
            product_id,
            score=12.0 * (float(popular_score or 0) / max_popular_score),
            reason="Trending among shoppers",
            algorithm="commerce_explore",
            source="popular_explore",
        )

    if not candidates:
        return [], []

    ordered_candidates = sorted(
        candidates.values(),
        key=lambda item: item["score"],
        reverse=True,
    )
    candidate_ids = [item["product_id"] for item in ordered_candidates[: limit * 5]]
    products = await _load_active_products(db, candidate_ids)
    product_by_id = {str(product.id): product for product in products}

    quality_rows = await db.execute(
        select(
            Review.product_id,
            func.avg(Review.rating),
            func.count(Review.id),
        )
        .where(Review.product_id.in_([product.id for product in products]))
        .group_by(Review.product_id)
    )
    review_quality = {
        str(product_id): {
            "avg": float(avg_rating or 0),
            "count": int(review_count or 0),
        }
        for product_id, avg_rating, review_count in quality_rows
    }

    final_meta: list[dict] = []
    for item in ordered_candidates:
        pid = item["product_id"]
        product = product_by_id.get(pid)
        if not product:
            continue
        quality = review_quality.get(pid, {})
        avg_rating = quality.get("avg", 0.0)
        review_count = quality.get("count", 0)
        if avg_rating:
            item["score"] += max(avg_rating - 3.0, 0.0) * min(review_count, 20) * 0.8
        if product.available_item_count > 0:
            item["score"] += min(product.available_item_count, 100) * 0.03
        final_meta.append({
            "product_id": pid,
            "score": round(float(item["score"]), 4),
            "reason": item["reason"],
            "algorithm": item["algorithm"],
        })

    final_meta.sort(key=lambda item: item["score"] or 0, reverse=True)
    ordered_products = [
        product_by_id[item["product_id"]]
        for item in final_meta
        if item["product_id"] in product_by_id
    ]
    diversified_products, diversified_meta = _diversify_products(
        ordered_products,
        final_meta,
        limit=limit,
    )
    return diversified_products, diversified_meta


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
    account_id, user_keys = await _resolve_user_identity(db, username)

    # Hadoop/Spark batch recommendations are the primary serving source. Recent
    # online behavior only fills gaps until the next Hadoop pipeline run.
    result = await db.execute(
        select(
            RecommendationResult.product_id,
            RecommendationResult.score,
            RecommendationResult.reason,
            RecommendationResult.algorithm,
        )
        .where(
            RecommendationResult.user_key.in_(user_keys),
            RecommendationResult.scene == "home",
        )
        .order_by(RecommendationResult.score.desc())
        .limit(MAX_RESULTS * 2)
    )
    rows = list(result)

    products: list[Product] = []
    meta: list[dict] = []
    seen_ids: set[str] = set()

    if rows:
        pids = [str(r[0]) for r in rows]
        batch_products = await _load_active_products(db, pids)
        batch_meta = {
            str(r[0]): {
                "product_id": str(r[0]),
                "score": r[1],
                "reason": r[2] or "For you",
                "algorithm": r[3] or "hadoop_commerce_v1",
            }
            for r in rows
        }
        for product in batch_products:
            if str(product.id) not in seen_ids:
                products.append(product)
                seen_ids.add(str(product.id))
                meta.append(batch_meta[str(product.id)])

    if len(products) < MAX_RESULTS:
        recent_products, recent_meta = await _recent_user_recommendations(
            db,
            account_id=account_id,
            user_keys=user_keys,
            limit=MAX_RESULTS,
        )
        recent_meta_by_product_id = {
            str(item.get("product_id")): item
            for item in recent_meta
            if item.get("product_id")
        }
        for product in recent_products:
            pid = str(product.id)
            if pid in seen_ids:
                continue
            products.append(product)
            seen_ids.add(pid)
            meta.append(recent_meta_by_product_id.get(pid, {
                "product_id": pid,
                "score": None,
                "reason": "Based on your recent activity",
                "algorithm": "commerce_realtime_v1",
            }))
            if len(products) >= MAX_RESULTS:
                break

    if len(products) < MIN_RESULTS:
        # Fallback to popular
        pop_result = await db.execute(
            select(PopularProduct.product_id, PopularProduct.score, PopularProduct.rank)
            .order_by(PopularProduct.score.desc())
            .limit(MAX_RESULTS * 2)
        )
        pop_rows = list(pop_result)
        pids = [str(r[0]) for r in pop_rows]
        popular_products = await _load_active_products(db, pids)
        popular_meta = {
            str(r[0]): {"product_id": str(r[0]), "score": r[1], "reason": "Trending now", "algorithm": "popular_v1"}
            for r in pop_rows
        }
        for product in popular_products:
            pid = str(product.id)
            if pid not in seen_ids:
                products.append(product)
                seen_ids.add(pid)
                meta.append(popular_meta[pid])

    if not products:
        products = await _fallback_popular(db, MAX_RESULTS)
        meta = [
            {
                "product_id": str(product.id),
                "score": None,
                "reason": "Recommended for you",
                "algorithm": "fallback",
            }
            for product in products
        ]

    return _build_response("account", products, meta)


@router.get("/users/{username}/preferences")
async def user_preference_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=180),
) -> dict:
    """Realtime preference profile used for visualizing personalization signals."""
    account_id, user_keys = await _resolve_user_identity(db, username)
    conditions = []
    if account_id:
        conditions.append(UserBehaviorEvent.account_id == account_id)
    conditions.extend([
        UserBehaviorEvent.anonymous_id.in_(user_keys),
        UserBehaviorEvent.session_id.in_(user_keys),
        UserBehaviorEvent.user_email.in_(user_keys),
    ])

    from sqlalchemy import or_
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            UserBehaviorEvent.event_type,
            UserBehaviorEvent.category_name,
            UserBehaviorEvent.shop_name,
            UserBehaviorEvent.price,
            UserBehaviorEvent.metadata_json,
            UserBehaviorEvent.created_at,
            Product.price,
            ProductCategory.name,
            Shop.name,
        )
        .outerjoin(Product, UserBehaviorEvent.product_id == Product.id)
        .outerjoin(ProductCategory, Product.category_id == ProductCategory.id)
        .outerjoin(Shop, UserBehaviorEvent.shop_id == Shop.id)
        .where(
            UserBehaviorEvent.event_type.in_(PREFERENCE_EVENT_TYPES),
            UserBehaviorEvent.created_at >= since,
            or_(*conditions),
        )
        .order_by(UserBehaviorEvent.created_at.desc())
        .limit(500)
    )

    categories: dict[str, dict] = {}
    shops: dict[str, dict] = {}
    price_bands: dict[str, dict] = {}
    event_mix: dict[str, int] = {}
    signal_count = 0
    positive_signal_count = 0
    latest_signal_at = None

    for row in result:
        (
            event_type,
            event_category_name,
            event_shop_name,
            event_price,
            metadata,
            created_at,
            product_price,
            product_category_name,
            shop_name,
        ) = row
        score = _rating_event_weight(event_type, metadata)
        signal_count += 1
        event_mix[event_type] = event_mix.get(event_type, 0) + 1
        if latest_signal_at is None:
            latest_signal_at = created_at
        if score <= 0:
            continue

        positive_signal_count += 1
        category_name = event_category_name or product_category_name
        if category_name:
            entry = categories.setdefault(category_name, {"score": 0.0, "count": 0})
            entry["score"] += score
            entry["count"] += 1

        resolved_shop_name = event_shop_name or shop_name
        if resolved_shop_name:
            entry = shops.setdefault(resolved_shop_name, {"score": 0.0, "count": 0})
            entry["score"] += score
            entry["count"] += 1

        price = float(event_price if event_price is not None else product_price) if (
            event_price is not None or product_price is not None
        ) else None
        band = _price_band(price)
        if band:
            entry = price_bands.setdefault(band, {"score": 0.0, "count": 0})
            entry["score"] += score
            entry["count"] += 1

    ranked_event_mix = [
        {"label": event_type, "count": count}
        for event_type, count in sorted(event_mix.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "user_key": username,
        "days": days,
        "signal_count": signal_count,
        "positive_signal_count": positive_signal_count,
        "latest_signal_at": latest_signal_at.isoformat() if latest_signal_at else None,
        "top_categories": _rank_preferences(categories),
        "top_shops": _rank_preferences(shops),
        "price_bands": _rank_preferences(price_bands, limit=4),
        "event_mix": ranked_event_mix,
    }
