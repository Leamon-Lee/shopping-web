"""Recommendation result tables — persisted output of Spark recommendation jobs."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from online_shopping.models import Base


class RecommendationResult(Base):
    """Per-user/scene recommendation results."""
    __tablename__ = "recommendation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    scene: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False, default="rule_v1")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ItemSimilarity(Base):
    """Pre-computed item-item similarity pairs."""
    __tablename__ = "item_similarities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    similar_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False, default="itemcf_v1")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PopularProduct(Base):
    """Cached popular/trending product rankings."""
    __tablename__ = "popular_products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scene: Mapped[str | None] = mapped_column(String(32), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
