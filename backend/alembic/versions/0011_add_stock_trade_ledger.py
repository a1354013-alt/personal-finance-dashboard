"""add stock trade ledger

Revision ID: 0011_add_stock_trade_ledger
Revises: 0010_enforce_unique_stock_holdings
Create Date: 2026-07-19 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0011_add_stock_trade_ledger"
down_revision = "0010_enforce_unique_stock_holdings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_trades",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stock_code", sa.String(length=20), nullable=False),
        sa.Column("trade_type", sa.String(length=20), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("shares", sa.Numeric(18, 6), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("fee", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("tax", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("source_holding_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("shares > 0", name="ck_stock_trades_shares_positive"),
        sa.CheckConstraint("price >= 0", name="ck_stock_trades_price_nonnegative"),
        sa.CheckConstraint("fee >= 0", name="ck_stock_trades_fee_nonnegative"),
        sa.CheckConstraint("tax >= 0", name="ck_stock_trades_tax_nonnegative"),
        sa.CheckConstraint(
            "trade_type IN ('OPENING_BALANCE', 'BUY', 'SELL')",
            name="ck_stock_trades_trade_type_allowed",
        ),
    )
    op.create_index("ix_stock_trades_id", "stock_trades", ["id"])
    op.create_index("ix_stock_trades_user_id", "stock_trades", ["user_id"])
    op.create_index("ix_stock_trades_stock_code", "stock_trades", ["stock_code"])
    op.create_index("ix_stock_trades_trade_date", "stock_trades", ["trade_date"])
    op.create_index("ix_stock_trades_trade_type", "stock_trades", ["trade_type"])
    op.create_index(
        "ix_stock_trades_user_stock_date_type",
        "stock_trades",
        ["user_id", "stock_code", "trade_date", "trade_type"],
    )

    op.execute(
        """
        INSERT INTO stock_trades (
            user_id,
            stock_code,
            trade_type,
            trade_date,
            shares,
            price,
            fee,
            tax,
            currency,
            note,
            source,
            source_holding_id,
            created_at,
            updated_at
        )
        SELECT
            h.user_id,
            h.stock_code,
            'OPENING_BALANCE',
            DATE(COALESCE(h.created_at, CURRENT_TIMESTAMP)),
            h.shares,
            h.average_cost,
            0,
            0,
            h.currency,
            h.note,
            'migration_0011_backfill',
            h.id,
            COALESCE(h.created_at, CURRENT_TIMESTAMP),
            COALESCE(h.updated_at, COALESCE(h.created_at, CURRENT_TIMESTAMP))
        FROM stock_holdings h
        WHERE NOT EXISTS (
            SELECT 1
            FROM stock_trades t
            WHERE t.user_id = h.user_id
              AND t.stock_code = h.stock_code
              AND t.trade_type = 'OPENING_BALANCE'
              AND t.source_holding_id = h.id
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_stock_trades_id", table_name="stock_trades")
    op.drop_index("ix_stock_trades_user_stock_date_type", table_name="stock_trades")
    op.drop_index("ix_stock_trades_trade_type", table_name="stock_trades")
    op.drop_index("ix_stock_trades_trade_date", table_name="stock_trades")
    op.drop_index("ix_stock_trades_stock_code", table_name="stock_trades")
    op.drop_index("ix_stock_trades_user_id", table_name="stock_trades")
    op.drop_table("stock_trades")
