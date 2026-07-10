from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_add_recurring_transactions"
down_revision = "0006_add_stock_price_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recurring_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("frequency", sa.String(length=10), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("next_run_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_recurring_transactions_id", "recurring_transactions", ["id"])
    op.create_index("ix_recurring_transactions_user_id", "recurring_transactions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_recurring_transactions_user_id", table_name="recurring_transactions")
    op.drop_index("ix_recurring_transactions_id", table_name="recurring_transactions")
    op.drop_table("recurring_transactions")
