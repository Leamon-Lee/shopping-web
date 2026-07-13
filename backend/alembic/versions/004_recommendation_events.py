"""User behavior events and recommendation cache tables.

Revision ID: 004
Revises: 003
Create Date: 2026-07-13
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_behavior_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.String(128), nullable=True),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shops.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_ube_account", "user_behavior_events", ["account_id"])
    op.create_index("idx_ube_session", "user_behavior_events", ["session_id"])
    op.create_index("idx_ube_type", "user_behavior_events", ["event_type"])
    op.create_index("idx_ube_product", "user_behavior_events", ["product_id"])
    op.create_index("idx_ube_shop", "user_behavior_events", ["shop_id"])
    op.create_index("idx_ube_created", "user_behavior_events", ["created_at"])
    # Composite index for common recommendation queries
    op.create_index("idx_ube_type_product_time", "user_behavior_events", ["event_type", "product_id", "created_at"])

    op.create_table(
        "recommendation_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=True),
        sa.Column("recommended_product_ids", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("reason_type", sa.String(32), nullable=False, server_default="rule_based"),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_rec_cache_product", "recommendation_cache", ["product_id"])
    op.create_index("idx_rec_cache_type", "recommendation_cache", ["reason_type"])


def downgrade() -> None:
    op.drop_table("recommendation_cache")
    op.drop_table("user_behavior_events")
