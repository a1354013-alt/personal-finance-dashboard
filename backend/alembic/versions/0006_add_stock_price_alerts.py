from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_add_stock_price_alerts"
down_revision = "0005_add_transaction_import_batches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_price_alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("watchlist_item_id", sa.Integer(), sa.ForeignKey("watchlist.id"), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("condition_type", sa.String(length=10), nullable=False),
        sa.Column("target_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("triggered_at", sa.DateTime(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("last_price_at_trigger", sa.Numeric(18, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_stock_price_alerts_user_id", "stock_price_alerts", ["user_id"])
    op.create_index("ix_stock_price_alerts_watchlist_item_id", "stock_price_alerts", ["watchlist_item_id"])
    op.create_index("ix_stock_price_alerts_symbol", "stock_price_alerts", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_stock_price_alerts_symbol", table_name="stock_price_alerts")
    op.drop_index("ix_stock_price_alerts_watchlist_item_id", table_name="stock_price_alerts")
    op.drop_index("ix_stock_price_alerts_user_id", table_name="stock_price_alerts")
    op.drop_table("stock_price_alerts")
