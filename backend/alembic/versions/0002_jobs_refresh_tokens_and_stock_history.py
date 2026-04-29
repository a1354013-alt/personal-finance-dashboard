from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_jobs_refresh_tokens_and_stock_history"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_price_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_code", sa.String(length=20), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(18, 4), nullable=True),
        sa.Column("high", sa.Numeric(18, 4), nullable=True),
        sa.Column("low", sa.Numeric(18, 4), nullable=True),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="yfinance"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("stock_code", "trade_date", name="_stock_history_date_uc"),
    )
    op.create_index("ix_stock_price_history_id", "stock_price_history", ["id"])
    op.create_index("ix_stock_price_history_stock_code", "stock_price_history", ["stock_code"])

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_sync_jobs_id", "sync_jobs", ["id"])
    op.create_index("ix_sync_jobs_job_type", "sync_jobs", ["job_type"])
    op.create_index("ix_sync_jobs_request_id", "sync_jobs", ["request_id"])
    op.create_index("ix_sync_jobs_status", "sync_jobs", ["status"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    op.execute(
        """
        INSERT INTO stock_price_history (stock_code, trade_date, open, high, low, close, volume, source, created_at)
        SELECT stock_code, trade_date, open, high, low, close, volume, 'yfinance', created_at
        FROM stock_prices
        """
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_sync_jobs_status", table_name="sync_jobs")
    op.drop_index("ix_sync_jobs_request_id", table_name="sync_jobs")
    op.drop_index("ix_sync_jobs_job_type", table_name="sync_jobs")
    op.drop_index("ix_sync_jobs_id", table_name="sync_jobs")
    op.drop_table("sync_jobs")

    op.drop_index("ix_stock_price_history_stock_code", table_name="stock_price_history")
    op.drop_index("ix_stock_price_history_id", table_name="stock_price_history")
    op.drop_table("stock_price_history")
