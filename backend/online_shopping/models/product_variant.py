from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Numeric, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from online_shopping.models import Base

if TYPE_CHECKING:
    from online_shopping.models.cart import CartItem
    from online_shopping.models.product import Product


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id_str: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="cny")
    inventory_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    manages_inventory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allows_backorder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product: Mapped[Product] = relationship("Product", back_populates="variants")
    cart_items: Mapped[list[CartItem]] = relationship("CartItem", back_populates="variant")
