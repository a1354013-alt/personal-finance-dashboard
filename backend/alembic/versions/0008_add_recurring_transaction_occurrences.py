"""add recurring transaction occurrences

Revision ID: 0008_add_recurring_transaction_occurrences
Revises: 0007_add_recurring_transactions
Create Date: 2026-07-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_add_recurring_transaction_occurrences"
down_revision = "0007_add_recurring_transactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recurring_transaction_occurrences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recurring_transaction_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("generated_expense_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["generated_expense_id"], ["expenses.id"]),
        sa.ForeignKeyConstraint(["recurring_transaction_id"], ["recurring_transactions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "recurring_transaction_id",
            "scheduled_date",
            name="uq_recurring_transaction_occurrence_schedule",
        ),
    )
    op.create_index(
        "ix_recurring_transaction_occurrences_id",
        "recurring_transaction_occurrences",
        ["id"],
    )
    op.create_index(
        "ix_recurring_transaction_occurrences_recurring_transaction_id",
        "recurring_transaction_occurrences",
        ["recurring_transaction_id"],
    )
    op.create_index(
        "ix_recurring_transaction_occurrences_user_id",
        "recurring_transaction_occurrences",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recurring_transaction_occurrences_user_id",
        table_name="recurring_transaction_occurrences",
    )
    op.drop_index(
        "ix_recurring_transaction_occurrences_recurring_transaction_id",
        table_name="recurring_transaction_occurrences",
    )
    op.drop_index(
        "ix_recurring_transaction_occurrences_id",
        table_name="recurring_transaction_occurrences",
    )
    op.drop_table("recurring_transaction_occurrences")
