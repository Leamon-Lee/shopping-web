"""Review model — customer product reviews."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from online_shopping.models import Base

if TYPE_CHECKING:
    from online_shopping.models.account import Account
    from online_shopping.models.product import Product


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    title: Mapped[str | None] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    account: Mapped[Account] = relationship("Account")
    product: Mapped[Product] = relationship("Product")
