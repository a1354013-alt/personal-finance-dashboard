from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_extend_watchlist_for_taiwan_stock_ai"
down_revision = "0003_align_budgets_schema_with_orm"
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "watchlist" not in inspector.get_table_names():
        return

    with op.batch_alter_table("watchlist") as batch_op:
        if not _has_column(inspector, "watchlist", "market"):
            batch_op.add_column(sa.Column("market", sa.String(length=50), nullable=True))
        if not _has_column(inspector, "watchlist", "exchange"):
            batch_op.add_column(sa.Column("exchange", sa.String(length=20), nullable=True))
        if not _has_column(inspector, "watchlist", "currency"):
            batch_op.add_column(sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"))
        if not _has_column(inspector, "watchlist", "last_price"):
            batch_op.add_column(sa.Column("last_price", sa.Numeric(18, 4), nullable=True))
        if not _has_column(inspector, "watchlist", "previous_close"):
            batch_op.add_column(sa.Column("previous_close", sa.Numeric(18, 4), nullable=True))
        if not _has_column(inspector, "watchlist", "price_change"):
            batch_op.add_column(sa.Column("price_change", sa.Numeric(18, 4), nullable=True))
        if not _has_column(inspector, "watchlist", "change_percent"):
            batch_op.add_column(sa.Column("change_percent", sa.Numeric(18, 6), nullable=True))
        if not _has_column(inspector, "watchlist", "volume"):
            batch_op.add_column(sa.Column("volume", sa.BigInteger(), nullable=True))
        if not _has_column(inspector, "watchlist", "provider"):
            batch_op.add_column(sa.Column("provider", sa.String(length=50), nullable=True))
        if not _has_column(inspector, "watchlist", "price_updated_at"):
            batch_op.add_column(sa.Column("price_updated_at", sa.DateTime(), nullable=True))
        if not _has_column(inspector, "watchlist", "sync_status"):
            batch_op.add_column(
                sa.Column("sync_status", sa.String(length=20), nullable=False, server_default="sync_required")
            )
        if not _has_column(inspector, "watchlist", "sync_required"):
            batch_op.add_column(sa.Column("sync_required", sa.Integer(), nullable=False, server_default="1"))
        if not _has_column(inspector, "watchlist", "sync_error"):
            batch_op.add_column(sa.Column("sync_error", sa.Text(), nullable=True))
        if not _has_column(inspector, "watchlist", "ai_summary"):
            batch_op.add_column(sa.Column("ai_summary", sa.Text(), nullable=True))
        if not _has_column(inspector, "watchlist", "ai_risk_notes"):
            batch_op.add_column(sa.Column("ai_risk_notes", sa.Text(), nullable=True))
        if not _has_column(inspector, "watchlist", "ai_updated_at"):
            batch_op.add_column(sa.Column("ai_updated_at", sa.DateTime(), nullable=True))

    bind.execute(
        sa.text(
            """
            UPDATE watchlist
            SET market = CASE
                    WHEN stock_code LIKE '%.TW' OR stock_code LIKE '%.TWO' THEN 'Taiwan'
                    ELSE COALESCE(market, 'US')
                END,
                exchange = CASE
                    WHEN stock_code LIKE '%.TW' THEN 'TWSE'
                    WHEN stock_code LIKE '%.TWO' THEN 'TPEx'
                    ELSE exchange
                END,
                currency = CASE
                    WHEN stock_code LIKE '%.TW' OR stock_code LIKE '%.TWO' THEN 'TWD'
                    ELSE COALESCE(currency, 'USD')
                END,
                provider = COALESCE(provider, 'yfinance'),
                sync_status = CASE
                    WHEN price_sync_status = 'success' THEN 'ready'
                    WHEN price_sync_status = 'failed' THEN 'error'
                    ELSE 'sync_required'
                END,
                sync_required = CASE WHEN price_sync_status = 'success' THEN 0 ELSE 1 END,
                sync_error = COALESCE(sync_error, last_sync_error)
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "watchlist" not in inspector.get_table_names():
        return

    with op.batch_alter_table("watchlist") as batch_op:
        for column_name in [
            "ai_updated_at",
            "ai_risk_notes",
            "ai_summary",
            "sync_error",
            "sync_required",
            "sync_status",
            "price_updated_at",
            "provider",
            "volume",
            "change_percent",
            "price_change",
            "previous_close",
            "last_price",
            "currency",
            "exchange",
            "market",
        ]:
            if _has_column(inspector, "watchlist", column_name):
                batch_op.drop_column(column_name)
