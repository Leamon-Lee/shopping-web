"""Recommendation cache — pre-computed product recommendations.

Populated by:
- Online: rule-based heuristics from user_behavior_events (real-time)
- Offline: Spark batch jobs via HDFS → PostgreSQL import
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from online_shopping.models import Base


class RecommendationCache(Base):
    __tablename__ = "recommendation_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # The source/seed product (NULL for global recommendations like "trending")
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Ordered list of recommended product IDs
    recommended_product_ids: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=[])
    # Human-readable reason for display
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Algorithm type for traceability
    reason_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="rule_based"
    )  # rule_based, itemcf, popular, trending, because_you_viewed
    # Score/confidence
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Freshness
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships for eager-loading recommended products
    @property
    def product_ids(self) -> list[str]:
        return [p["product_id"] for p in self.recommended_product_ids if "product_id" in p]
