from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from models.budget import BudgetORM
from models.expense import ExpenseORM


@dataclass
class MonthRange:
    month_start: date
    next_month_start: date


def get_month_range(reference_date: date | None = None) -> MonthRange:
    current = reference_date or date.today()
    month_start = current.replace(day=1)
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)
    return MonthRange(month_start=month_start, next_month_start=next_month_start)


def get_month_expense_rows(
    db: Session,
    user_id: int,
    reference_date: date | None = None,
) -> list[ExpenseORM]:
    month_range = get_month_range(reference_date)
    return (
        db.query(ExpenseORM)
        .filter(
            ExpenseORM.user_id == user_id,
            ExpenseORM.type == "expense",
            ExpenseORM.date >= month_range.month_start,
            ExpenseORM.date < month_range.next_month_start,
        )
        .all()
    )


def get_current_month_spend_by_category(
    db: Session,
    user_id: int,
    reference_date: date | None = None,
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for expense in get_month_expense_rows(db, user_id, reference_date):
        totals[expense.category] += Decimal(expense.amount)
    return dict(totals)


def build_budget_status(
    db: Session,
    user_id: int,
    reference_date: date | None = None,
) -> list[dict]:
    spend_by_category = get_current_month_spend_by_category(db, user_id, reference_date)
    budgets = (
        db.query(BudgetORM)
        .filter(BudgetORM.user_id == user_id)
        .order_by(BudgetORM.category.asc())
        .all()
    )

    budget_status = []
    for budget in budgets:
        monthly_limit = Decimal(budget.monthly_limit)
        spent = spend_by_category.get(budget.category, Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        percent_used = round((float(spent) / float(monthly_limit)) * 100, 2) if monthly_limit else 0.0
        budget_status.append(
            {
                "id": budget.id,
                "user_id": budget.user_id,
                "category": budget.category,
                "monthly_limit": monthly_limit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "created_at": budget.created_at,
                "current_spent": spent,
                "percent_used": percent_used,
                "over_budget": spent > monthly_limit,
            }
        )

    return budget_status
