"""Shop model — a store owned by a manager account."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from online_shopping.models import Base

if TYPE_CHECKING:
    from online_shopping.models.account import Account
    from online_shopping.models.product import Product


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")  # pending, active, disabled, rejected
    category: Mapped[str | None] = mapped_column(String(120))
    logo_url: Mapped[str | None] = mapped_column(String(512))
    banner_url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner: Mapped[Account] = relationship("Account", back_populates="shops")


class ShopProduct(Base):
    """Join table linking shops to products (many-to-many)."""
    __tablename__ = "shop_products"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
