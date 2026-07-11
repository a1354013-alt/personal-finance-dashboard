"""add stock holdings

Revision ID: 0009_add_stock_holdings
Revises: 0008_add_recurring_transaction_occurrences
Create Date: 2026-07-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_add_stock_holdings"
down_revision = "0008_add_recurring_transaction_occurrences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_holdings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("stock_code", sa.String(length=20), nullable=False),
        sa.Column("shares", sa.Numeric(18, 6), nullable=False),
        sa.Column("average_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_holdings_id", "stock_holdings", ["id"])
    op.create_index("ix_stock_holdings_user_id", "stock_holdings", ["user_id"])
    op.create_index("ix_stock_holdings_stock_code", "stock_holdings", ["stock_code"])


def downgrade() -> None:
    op.drop_index("ix_stock_holdings_stock_code", table_name="stock_holdings")
    op.drop_index("ix_stock_holdings_user_id", table_name="stock_holdings")
    op.drop_index("ix_stock_holdings_id", table_name="stock_holdings")
    op.drop_table("stock_holdings")
