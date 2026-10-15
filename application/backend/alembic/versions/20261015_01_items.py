"""create items table

Revision ID: 20261015_01
Revises:
Create Date: 2026-10-15
"""
import sqlalchemy as sa
from alembic import op

revision = "20261015_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("sku", sa.String(40), nullable=False),
        sa.Column("category", sa.String(60), nullable=False, server_default="General"),
        sa.Column("supplier", sa.String(120), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("quantity >= 0", name="ck_items_quantity_non_negative"),
    )
    op.create_index("ix_items_sku", "items", ["sku"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_items_sku", table_name="items")
    op.drop_table("items")
