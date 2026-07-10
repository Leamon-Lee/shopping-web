from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from online_shopping.models import Base

if TYPE_CHECKING:
    from online_shopping.models.address import Address
    from online_shopping.models.order import Order
    from online_shopping.models.shop import Shop


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone_country_code: Mapped[str | None] = mapped_column(String(16))
    phone_number: Mapped[str | None] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="customer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    addresses: Mapped[list[Address]] = relationship("Address", back_populates="account", cascade="all, delete-orphan")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="account")
    shops: Mapped[list[Shop]] = relationship("Shop", back_populates="owner")
