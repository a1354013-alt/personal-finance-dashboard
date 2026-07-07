from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_add_transaction_import_batches"
down_revision = "0004_extend_watchlist_for_taiwan_stock_ai"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transaction_import_batches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=10), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invalid_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="previewed"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_transaction_import_batches_user_id", "transaction_import_batches", ["user_id"])

    op.create_table(
        "transaction_import_rows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.String(length=36), sa.ForeignKey("transaction_import_batches.id"), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=False),
        sa.Column("normalized_date", sa.Date(), nullable=True),
        sa.Column("normalized_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("normalized_type", sa.String(length=10), nullable=True),
        sa.Column("normalized_category", sa.String(length=50), nullable=True),
        sa.Column("normalized_note", sa.Text(), nullable=True),
        sa.Column("payment_method", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="invalid"),
        sa.Column("validation_errors", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("duplicate_reasons", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(length=255), nullable=True),
        sa.Column("created_expense_id", sa.Integer(), sa.ForeignKey("expenses.id"), nullable=True),
    )
    op.create_index("ix_transaction_import_rows_batch_id", "transaction_import_rows", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_transaction_import_rows_batch_id", table_name="transaction_import_rows")
    op.drop_table("transaction_import_rows")
    op.drop_index("ix_transaction_import_batches_user_id", table_name="transaction_import_batches")
    op.drop_table("transaction_import_batches")
