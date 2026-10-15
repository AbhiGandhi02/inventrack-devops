"""create stock_movements table

Revision ID: 20261015_02
Revises: 20261015_01
Create Date: 2026-10-15
"""
import sqlalchemy as sa
from alembic import op

revision = "20261015_02"
down_revision = "20261015_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("change", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(200), nullable=False, server_default=""),
        sa.Column("quantity_after", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_stock_movements_item_id", "stock_movements", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_stock_movements_item_id", table_name="stock_movements")
    op.drop_table("stock_movements")
