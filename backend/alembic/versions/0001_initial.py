from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("ix_expenses_id", "expenses", ["id"])

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("monthly_limit", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "category", name="_user_budget_category_uc"),
    )
    op.create_index("ix_budgets_id", "budgets", ["id"])

    op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stock_code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("price_sync_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
        sa.Column("last_sync_attempt_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "stock_code", name="_user_stock_uc"),
    )
    op.create_index("ix_watchlist_id", "watchlist", ["id"])

    op.create_table(
        "stock_prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_code", sa.String(length=20), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(18, 4), nullable=True),
        sa.Column("high", sa.Numeric(18, 4), nullable=True),
        sa.Column("low", sa.Numeric(18, 4), nullable=True),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("stock_code", "trade_date", name="_stock_date_uc"),
    )
    op.create_index("ix_stock_prices_id", "stock_prices", ["id"])
    op.create_index("ix_stock_prices_stock_code", "stock_prices", ["stock_code"])

    op.create_table(
        "fundamentals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_code", sa.String(length=20), nullable=False),
        sa.Column("pe_ratio", sa.Numeric(18, 6), nullable=True),
        sa.Column("pb_ratio", sa.Numeric(18, 6), nullable=True),
        sa.Column("dividend_yield", sa.Numeric(18, 6), nullable=True),
        sa.Column("revenue_growth", sa.Numeric(18, 6), nullable=True),
        sa.Column("eps", sa.Numeric(18, 6), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.UniqueConstraint("stock_code", "source", "as_of_date", name="_fundamentals_code_source_asof_uc"),
    )
    op.create_index("ix_fundamentals_id", "fundamentals", ["id"])
    op.create_index("ix_fundamentals_stock_code", "fundamentals", ["stock_code"])
    op.create_index("ix_fundamentals_stock_code_fetched_at", "fundamentals", ["stock_code", "fetched_at"])


def downgrade() -> None:
    op.drop_index("ix_fundamentals_stock_code_fetched_at", table_name="fundamentals")
    op.drop_index("ix_fundamentals_stock_code", table_name="fundamentals")
    op.drop_index("ix_fundamentals_id", table_name="fundamentals")
    op.drop_table("fundamentals")

    op.drop_index("ix_stock_prices_stock_code", table_name="stock_prices")
    op.drop_index("ix_stock_prices_id", table_name="stock_prices")
    op.drop_table("stock_prices")

    op.drop_index("ix_watchlist_id", table_name="watchlist")
    op.drop_table("watchlist")

    op.drop_index("ix_budgets_id", table_name="budgets")
    op.drop_table("budgets")

    op.drop_index("ix_expenses_id", table_name="expenses")
    op.drop_table("expenses")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

