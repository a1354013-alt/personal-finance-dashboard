"""enforce unique stock holdings

Revision ID: 0010_enforce_unique_stock_holdings
Revises: 0009_add_stock_holdings
Create Date: 2026-07-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from decimal import Decimal, ROUND_HALF_UP


revision = "0010_enforce_unique_stock_holdings"
down_revision = "0009_add_stock_holdings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    duplicate_groups = connection.execute(
        sa.text(
            """
            SELECT user_id, stock_code
            FROM stock_holdings
            GROUP BY user_id, stock_code
            HAVING COUNT(*) > 1
            """
        )
    ).mappings()
    for group in duplicate_groups:
        rows = connection.execute(
            sa.text(
                """
                SELECT id, shares, average_cost
                FROM stock_holdings
                WHERE user_id = :user_id AND stock_code = :stock_code
                ORDER BY id
                """
            ),
            {"user_id": group["user_id"], "stock_code": group["stock_code"]},
        ).mappings().all()
        keep_id = rows[0]["id"]
        # Historical duplicate rows are merged into the oldest row id. Currency, note,
        # created_at, and updated_at come from that surviving row; shares are summed,
        # and average_cost is the weighted cost rounded to the column's 4 decimals.
        total_shares = sum(Decimal(str(row["shares"])) for row in rows)
        total_cost = sum(Decimal(str(row["shares"])) * Decimal(str(row["average_cost"])) for row in rows)
        average_cost = (
            (total_cost / total_shares).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            if total_shares
            else Decimal(str(rows[0]["average_cost"]))
        )
        duplicate_ids = [row["id"] for row in rows[1:]]

        connection.execute(
            sa.text(
                """
                UPDATE stock_holdings
                SET shares = :shares, average_cost = :average_cost
                WHERE id = :keep_id
                """
            ),
            {"shares": str(total_shares), "average_cost": str(average_cost), "keep_id": keep_id},
        )
        connection.execute(
            sa.text("DELETE FROM stock_holdings WHERE id IN :duplicate_ids").bindparams(
                sa.bindparam("duplicate_ids", expanding=True)
            ),
            {"duplicate_ids": duplicate_ids},
        )

    with op.batch_alter_table("stock_holdings") as batch_op:
        batch_op.create_unique_constraint("_user_stock_holding_uc", ["user_id", "stock_code"])


def downgrade() -> None:
    with op.batch_alter_table("stock_holdings") as batch_op:
        batch_op.drop_constraint("_user_stock_holding_uc", type_="unique")
