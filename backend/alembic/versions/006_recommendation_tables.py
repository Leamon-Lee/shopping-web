"""Recommendation result storage tables.

Revision ID: 006
Revises: 005
Create Date: 2026-07-13
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_key", sa.String(255), nullable=True),
        sa.Column("scene", sa.String(32), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float, nullable=False, server_default="0"),
        sa.Column("rank", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("algorithm", sa.String(64), nullable=False, server_default="rule_v1"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_rec_res_user_scene", "recommendation_results", ["user_key", "scene"])
    op.create_index("idx_rec_res_scene", "recommendation_results", ["scene"])
    op.create_index("idx_rec_res_product", "recommendation_results", ["product_id"])

    op.create_table(
        "item_similarities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("similar_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float, nullable=False, server_default="0"),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("algorithm", sa.String(64), nullable=False, server_default="itemcf_v1"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_item_sim_product", "item_similarities", ["product_id"])
    op.create_index("idx_item_sim_pair", "item_similarities", ["product_id", "similar_product_id"], unique=True)

    op.create_table(
        "popular_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float, nullable=False, server_default="0"),
        sa.Column("rank", sa.Integer, nullable=False, server_default="0"),
        sa.Column("scene", sa.String(32), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_pop_product", "popular_products", ["product_id"])
    op.create_index("idx_pop_rank", "popular_products", ["rank"])


def downgrade() -> None:
    op.drop_table("popular_products")
    op.drop_table("item_similarities")
    op.drop_table("recommendation_results")
