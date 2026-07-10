"""Initial schema — accounts, products, orders, carts, shops, shipments, wishlist, reviews.

Revision ID: 001
Revises: None
Create Date: 2026-07-10
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Accounts
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_name", sa.String(20), unique=True, nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("first_name", sa.String(100), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(100), nullable=False, server_default=""),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("phone_country_code", sa.String(16)),
        sa.Column("phone_number", sa.String(64)),
        sa.Column("role", sa.String(32), nullable=False, server_default="customer"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Addresses
    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("street", sa.String(255), nullable=False),
        sa.Column("city", sa.String(120), nullable=False),
        sa.Column("state", sa.String(120), nullable=False, server_default=""),
        sa.Column("postal_code", sa.String(32), nullable=False, server_default=""),
        sa.Column("country", sa.String(120), nullable=False, server_default=""),
        sa.Column("is_default_shipping", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Product categories
    op.create_table(
        "product_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(120), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Shops
    op.create_table(
        "shops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("category", sa.String(120)),
        sa.Column("logo_url", sa.String(512)),
        sa.Column("banner_url", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Products
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_categories.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(160), unique=True, nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("available_item_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Product images
    op.create_table(
        "product_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.String(512), nullable=False),
        sa.Column("rank", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Product variants
    op.create_table(
        "product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id_str", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("sku", sa.String(64), unique=True, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="cny"),
        sa.Column("inventory_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("manages_inventory", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("allows_backorder", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Shop-Products join
    op.create_table(
        "shop_products",
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shops.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    )

    # Shopping carts
    op.create_table(
        "shopping_carts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True)),
        sa.Column("region_id", sa.String(64)),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="cny"),
        sa.Column("email", sa.String(255)),
        sa.Column("locale", sa.String(16)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Cart items
    op.create_table(
        "cart_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cart_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shopping_carts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Orders
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL")),
        sa.Column("order_number", sa.String(64), unique=True, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("order_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Order items
    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("product_name", sa.String(160), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Payments
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="CNY"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Shipments
    op.create_table(
        "shipments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("carrier", sa.String(100)),
        sa.Column("tracking_number", sa.String(100)),
        sa.Column("tracking_url", sa.String(512)),
        sa.Column("estimated_arrival", sa.DateTime(timezone=True)),
        sa.Column("shipped_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Wishlist items
    op.create_table(
        "wishlist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Reviews
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("content", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("wishlist_items")
    op.drop_table("shipments")
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("cart_items")
    op.drop_table("shopping_carts")
    op.drop_table("shop_products")
    op.drop_table("product_variants")
    op.drop_table("product_images")
    op.drop_table("products")
    op.drop_table("shops")
    op.drop_table("product_categories")
    op.drop_table("addresses")
    op.drop_table("accounts")
