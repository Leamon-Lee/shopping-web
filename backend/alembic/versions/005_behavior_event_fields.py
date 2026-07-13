"""Add rich event context fields to user_behavior_events.

Revision ID: 005
Revises: 004
Create Date: 2026-07-13
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Widen event_type
    op.alter_column("user_behavior_events", "event_type", type_=sa.String(64), existing_type=sa.String(32), nullable=False)

    # Who
    op.add_column("user_behavior_events", sa.Column("user_email", sa.String(255), nullable=True))
    op.add_column("user_behavior_events", sa.Column("anonymous_id", sa.String(128), nullable=True))
    op.create_index("idx_ube_anon", "user_behavior_events", ["anonymous_id"])

    # Product context (snapshot fields)
    op.add_column("user_behavior_events", sa.Column("product_name", sa.String(200), nullable=True))
    op.add_column("user_behavior_events", sa.Column("product_slug", sa.String(200), nullable=True))
    op.add_column("user_behavior_events", sa.Column("shop_name", sa.String(200), nullable=True))
    op.add_column("user_behavior_events", sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("user_behavior_events", sa.Column("category_name", sa.String(200), nullable=True))
    op.create_foreign_key("fk_ube_category", "user_behavior_events", "product_categories", ["category_id"], ["id"], ondelete="SET NULL")

    # Interaction details
    op.add_column("user_behavior_events", sa.Column("query", sa.String(500), nullable=True))
    op.add_column("user_behavior_events", sa.Column("quantity", sa.Integer, nullable=True))
    op.add_column("user_behavior_events", sa.Column("price", sa.Float, nullable=True))
    op.add_column("user_behavior_events", sa.Column("source_page", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("user_behavior_events", "source_page")
    op.drop_column("user_behavior_events", "price")
    op.drop_column("user_behavior_events", "quantity")
    op.drop_column("user_behavior_events", "query")
    op.drop_constraint("fk_ube_category", "user_behavior_events", type_="foreignkey")
    op.drop_column("user_behavior_events", "category_name")
    op.drop_column("user_behavior_events", "category_id")
    op.drop_column("user_behavior_events", "shop_name")
    op.drop_column("user_behavior_events", "product_slug")
    op.drop_column("user_behavior_events", "product_name")
    op.drop_index("idx_ube_anon", table_name="user_behavior_events")
    op.drop_column("user_behavior_events", "anonymous_id")
    op.drop_column("user_behavior_events", "user_email")
    op.alter_column("user_behavior_events", "event_type", type_=sa.String(32), existing_type=sa.String(64), nullable=False)
