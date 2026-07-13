"""User behavior event model for recommendation system.

Stores raw behavioral events that feed into:
- Real-time rule-based recommendations (same DB queries)
- Batch Spark/HDFS pipeline (export → ItemCF → import back)

Event types:
  product_view, search, add_to_cart, remove_from_cart,
  checkout_start, order_created, order_paid, favorite_product,
  recommendation_impression, recommendation_click, recommendation_add_to_cart
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from online_shopping.models import Base

VALID_EVENT_TYPES = frozenset({
    "product_view",
    "search",
    "add_to_cart",
    "remove_from_cart",
    "checkout_start",
    "order_created",
    "order_paid",
    "favorite_product",
    "recommendation_impression",
    "recommendation_click",
    "recommendation_add_to_cart",
})


class UserBehaviorEvent(Base):
    __tablename__ = "user_behavior_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Event identity ────────────────────────────────────────────
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # ── Who (resolved at record time) ─────────────────────────────
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    anonymous_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # ── What (product context) ────────────────────────────────────
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    product_slug: Mapped[str | None] = mapped_column(String(200), nullable=True)
    shop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="SET NULL"), nullable=True, index=True
    )
    shop_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True
    )
    category_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # ── Interaction details ───────────────────────────────────────
    query: Mapped[str | None] = mapped_column(String(500), nullable=True)      # search query
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)       # cart/order qty
    price: Mapped[float | None] = mapped_column(Float, nullable=True)          # unit price at event time
    source_page: Mapped[str | None] = mapped_column(String(500), nullable=True)  # URL path

    # ── Extensible payload ────────────────────────────────────────
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default={})

    # ── Timestamp ─────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
