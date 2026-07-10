"""Shipment model — tracks order fulfillment and delivery."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from online_shopping.models import Base

if TYPE_CHECKING:
    from online_shopping.models.order import Order


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    carrier: Mapped[str | None] = mapped_column(String(100))
    tracking_number: Mapped[str | None] = mapped_column(String(100))
    tracking_url: Mapped[str | None] = mapped_column(String(512))
    estimated_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order: Mapped[Order] = relationship("Order", back_populates="shipments")
