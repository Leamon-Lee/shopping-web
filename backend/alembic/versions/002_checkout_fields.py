"""Add checkout JSONB fields to shopping_carts and orders.

Revision ID: 002
Revises: 001
Create Date: 2026-07-13
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # shopping_carts: add checkout state columns
    op.add_column(
        "shopping_carts",
        sa.Column("shipping_address", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "shopping_carts",
        sa.Column("billing_address", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "shopping_carts",
        sa.Column("shipping_method", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "shopping_carts",
        sa.Column("payment_session", postgresql.JSONB, nullable=True),
    )

    # orders: add checkout metadata columns
    op.add_column(
        "orders",
        sa.Column("email", sa.String(255), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("shipping_address", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("billing_address", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("shipping_method", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "shipping_method")
    op.drop_column("orders", "billing_address")
    op.drop_column("orders", "shipping_address")
    op.drop_column("orders", "email")
    op.drop_column("shopping_carts", "payment_session")
    op.drop_column("shopping_carts", "shipping_method")
    op.drop_column("shopping_carts", "billing_address")
    op.drop_column("shopping_carts", "shipping_address")
