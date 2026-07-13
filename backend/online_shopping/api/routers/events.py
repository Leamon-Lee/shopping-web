"""User behavior event tracking API.

Fire-and-forget endpoints for collecting behavioral data.
All events are stored in PostgreSQL and can later be exported to HDFS.

Supported event types:
  product_view, search, add_to_cart, remove_from_cart,
  checkout_start, order_created, order_paid, favorite_product,
  recommendation_impression, recommendation_click, recommendation_add_to_cart
"""

import csv
import io

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db, get_optional_user
from online_shopping.models.account import Account
from online_shopping.models.user_behavior_event import UserBehaviorEvent, VALID_EVENT_TYPES

router = APIRouter()

# ── Schema ───────────────────────────────────────────────────────

class TrackEventPayload(BaseModel):
    event_type: str = Field(min_length=1, max_length=64)
    # Product context (all optional — some events like "search" have no product)
    product_id: str | None = None
    product_name: str | None = None
    product_slug: str | None = None
    shop_id: str | None = None
    shop_name: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    # Interaction
    query: str | None = None
    quantity: int | None = None
    price: float | None = None
    source_page: str | None = None
    # User identity (optional — backend auto-fills from auth/session)
    session_id: str | None = None
    anonymous_id: str | None = None
    # Extensible
    metadata: dict | None = None


def _try_uuid(value: str | None):
    if not value:
        return None
    import uuid as _uuid
    try:
        return _uuid.UUID(value)
    except (ValueError, TypeError):
        return None


# ── POST /events ──────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def track_event(
    payload: TrackEventPayload,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
    x_anonymous_id: str | None = Header(None, alias="X-Anonymous-Id"),
) -> dict:
    """Record a user behavior event.  Returns 202 — fire-and-forget.

    The backend auto-fills:
      - account_id / user_email from the authenticated user
      - session_id from X-Session-Id header if not in payload
      - anonymous_id from X-Anonymous-Id header if not in payload
    """
    # Validate event_type
    if payload.event_type not in VALID_EVENT_TYPES:
        return {"status": "rejected", "reason": f"Unknown event_type: {payload.event_type}"}

    event = UserBehaviorEvent(
        event_type=payload.event_type,
        # Who — resolved at record time
        account_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else None,
        anonymous_id=payload.anonymous_id or x_anonymous_id,
        session_id=payload.session_id or x_session_id,
        # What
        product_id=_try_uuid(payload.product_id),
        product_name=payload.product_name,
        product_slug=payload.product_slug,
        shop_id=_try_uuid(payload.shop_id),
        shop_name=payload.shop_name,
        category_id=_try_uuid(payload.category_id),
        category_name=payload.category_name,
        # Interaction
        query=payload.query,
        quantity=payload.quantity,
        price=payload.price,
        source_page=payload.source_page,
        # Extensible
        metadata_json=payload.metadata or {},
    )
    db.add(event)
    await db.commit()

    return {"status": "recorded", "event_id": str(event.id)}


# ── GET /events/stats ─────────────────────────────────────────────

@router.get("/stats")
async def event_stats(
    db: AsyncSession = Depends(get_db),
    days: int = Query(7, ge=1, le=90),
) -> dict:
    """Get event statistics for monitoring."""
    total = await db.execute(select(func.count(UserBehaviorEvent.id)))
    by_type = await db.execute(
        select(
            UserBehaviorEvent.event_type,
            func.count(UserBehaviorEvent.id),
        ).group_by(UserBehaviorEvent.event_type)
    )

    recent = await db.execute(
        select(func.count(UserBehaviorEvent.id)).where(
            UserBehaviorEvent.created_at >= func.now() - func.make_interval(days := days)
        )
    )

    return {
        "total_events": total.scalar() or 0,
        f"events_last_{days}_days": recent.scalar() or 0,
        "by_type": {row[0]: row[1] for row in by_type},
    }


# ── GET /events/export ────────────────────────────────────────────

@router.get("/export")
async def export_events(
    db: AsyncSession = Depends(get_db),
    event_type: str | None = Query(None),
    days: int = Query(1, ge=1, le=90),
    limit: int = Query(10000, ge=1, le=100000),
    offset: int = Query(0, ge=0),
    format: str = Query("json", pattern="^(json|csv)$"),
) -> dict:
    """Export events for batch processing (e.g., Spark ingestion).

    Paginated, filterable by event_type and date range.
    Returns JSON by default; set format=csv for CSV download.
    """
    from sqlalchemy import text as _text

    conditions = ["1=1"]
    params: dict = {"lim": limit, "off": offset}

    if event_type:
        conditions.append("event_type = :etype")
        params["etype"] = event_type
    if days:
        conditions.append("created_at >= now() - make_interval(days => :days)")
        params["days"] = days

    where_clause = " AND ".join(conditions)

    rows_result = await db.execute(
        _text(f"""
            SELECT id, event_type, account_id, user_email, anonymous_id, session_id,
                   product_id, product_name, product_slug,
                   shop_id, shop_name,
                   category_id, category_name,
                   query, quantity, price, source_page,
                   metadata_json, created_at
            FROM user_behavior_events
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :lim OFFSET :off
        """),
        params,
    )

    count_result = await db.execute(
        _text(f"SELECT COUNT(*) FROM user_behavior_events WHERE {where_clause}"),
        {k: v for k, v in params.items() if k not in ("lim", "off")},
    )

    columns = [
        "id", "event_type", "account_id", "user_email", "anonymous_id", "session_id",
        "product_id", "product_name", "product_slug",
        "shop_id", "shop_name",
        "category_id", "category_name",
        "query", "quantity", "price", "source_page",
        "metadata_json", "created_at",
    ]

    rows = []
    for row in rows_result:
        d: dict = {}
        for i, col in enumerate(columns):
            val = row[i]
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            d[col] = str(val) if val is not None else ""
        rows.append(d)

    # Return CSV when requested
    if format == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=events_export.csv"},
        )

    return {
        "count": count_result.scalar() or 0,
        "limit": limit,
        "offset": offset,
        "has_more": len(rows) == limit,
        "events": rows,
    }
