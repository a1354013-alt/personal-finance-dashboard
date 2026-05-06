from __future__ import annotations

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision = "0003_align_budgets_schema_with_orm"
down_revision = "0002_jobs_refresh_tokens_and_stock_history"
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_unique(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    return any(constraint["name"] == constraint_name for constraint in inspector.get_unique_constraints(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    now = datetime.now(timezone.utc)

    if "budgets" not in inspector.get_table_names():
        return

    has_month = _has_column(inspector, "budgets", "month")
    has_amount = _has_column(inspector, "budgets", "amount")
    has_monthly_limit = _has_column(inspector, "budgets", "monthly_limit")
    has_created_at = _has_column(inspector, "budgets", "created_at")
    has_updated_at = _has_column(inspector, "budgets", "updated_at")

    with op.batch_alter_table("budgets") as batch_op:
        if not has_month:
            batch_op.add_column(sa.Column("month", sa.String(length=7), nullable=True))
        if not has_amount:
            batch_op.add_column(sa.Column("amount", sa.Numeric(18, 2), nullable=True))
        if not has_created_at:
            batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        if not has_updated_at:
            batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))

    if has_monthly_limit:
        bind.execute(
            sa.text(
                """
                UPDATE budgets
                SET amount = COALESCE(amount, monthly_limit)
                """
            )
        )

    bind.execute(
        sa.text(
            """
            UPDATE budgets
            SET month = COALESCE(NULLIF(month, ''), '1970-01'),
                created_at = COALESCE(created_at, :now),
                updated_at = COALESCE(updated_at, created_at, :now),
                amount = COALESCE(amount, 0)
            """
        ),
        {"now": now},
    )

    inspector = sa.inspect(bind)
    with op.batch_alter_table("budgets") as batch_op:
        if _has_unique(inspector, "budgets", "_user_budget_category_uc"):
            batch_op.drop_constraint("_user_budget_category_uc", type_="unique")
        if _has_unique(inspector, "budgets", "_user_month_category_uc"):
            batch_op.drop_constraint("_user_month_category_uc", type_="unique")
        batch_op.alter_column("month", existing_type=sa.String(length=7), nullable=False)
        batch_op.alter_column("amount", existing_type=sa.Numeric(18, 2), nullable=False)
        batch_op.alter_column("created_at", existing_type=sa.DateTime(), nullable=False)
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(), nullable=False)
        if has_monthly_limit:
            batch_op.drop_column("monthly_limit")
        batch_op.create_unique_constraint("_user_month_category_uc", ["user_id", "month", "category"])

    inspector = sa.inspect(bind)
    if not _has_index(inspector, "budgets", "ix_budgets_month"):
        op.create_index("ix_budgets_month", "budgets", ["month"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "budgets" not in inspector.get_table_names():
        return

    has_monthly_limit = _has_column(inspector, "budgets", "monthly_limit")
    with op.batch_alter_table("budgets") as batch_op:
        if _has_unique(inspector, "budgets", "_user_month_category_uc"):
            batch_op.drop_constraint("_user_month_category_uc", type_="unique")
        if not has_monthly_limit:
            batch_op.add_column(sa.Column("monthly_limit", sa.Numeric(18, 2), nullable=True))

    bind.execute(sa.text("UPDATE budgets SET monthly_limit = COALESCE(monthly_limit, amount)"))

    inspector = sa.inspect(bind)
    with op.batch_alter_table("budgets") as batch_op:
        batch_op.alter_column("monthly_limit", existing_type=sa.Numeric(18, 2), nullable=False)
        if _has_column(inspector, "budgets", "updated_at"):
            batch_op.drop_column("updated_at")
        if _has_column(inspector, "budgets", "month"):
            batch_op.drop_column("month")
        if _has_column(inspector, "budgets", "amount"):
            batch_op.drop_column("amount")
        batch_op.create_unique_constraint("_user_budget_category_uc", ["user_id", "category"])

    inspector = sa.inspect(bind)
    if _has_index(inspector, "budgets", "ix_budgets_month"):
        op.drop_index("ix_budgets_month", table_name="budgets")
