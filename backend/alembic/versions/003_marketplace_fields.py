"""Multi-vendor marketplace fields: security, ownership, product status.

Revision ID: 003
Revises: 002
Create Date: 2026-07-13
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # orders: guest security + cart tracking
    op.add_column("orders", sa.Column("cart_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("orders", sa.Column("order_access_token", sa.String(128), nullable=True))
    op.create_index("idx_orders_access_token", "orders", ["order_access_token"], unique=False)

    # order_items: multi-vendor shop ownership
    op.add_column("order_items", sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("order_items", sa.Column("shop_name", sa.String(200), nullable=True))
    op.create_foreign_key("fk_order_items_shop", "order_items", "shops", ["shop_id"], ["id"], ondelete="SET NULL")
    op.create_index("idx_order_items_shop", "order_items", ["shop_id"])

    # products: visibility status for marketplace moderation
    op.add_column("products", sa.Column("status", sa.String(32), nullable=False, server_default="active"))
    op.create_index("idx_products_status", "products", ["status"])

    # shipments: shop ownership for multi-vendor fulfillment
    op.add_column("shipments", sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_shipments_shop", "shipments", "shops", ["shop_id"], ["id"], ondelete="SET NULL")
    op.create_index("idx_shipments_shop", "shipments", ["shop_id"])


def downgrade() -> None:
    op.drop_index("idx_shipments_shop", table_name="shipments")
    op.drop_constraint("fk_shipments_shop", "shipments", type_="foreignkey")
    op.drop_column("shipments", "shop_id")

    op.drop_index("idx_products_status", table_name="products")
    op.drop_column("products", "status")

    op.drop_index("idx_order_items_shop", table_name="order_items")
    op.drop_constraint("fk_order_items_shop", "order_items", type_="foreignkey")
    op.drop_column("order_items", "shop_name")
    op.drop_column("order_items", "shop_id")

    op.drop_index("idx_orders_access_token", table_name="orders")
    op.drop_column("orders", "order_access_token")
    op.drop_column("orders", "cart_id")
