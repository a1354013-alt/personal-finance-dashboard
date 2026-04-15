from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.expense import ExpenseORM
from models.dashboard import DashboardSummaryResponse
from models.user import UserORM
from services.auth import get_current_user
from services.budget_summary import build_budget_status

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    all_records = db.query(ExpenseORM).filter(ExpenseORM.user_id == current_user.id).all()

    total_income = sum((Decimal(r.amount) for r in all_records if r.type == "income"), start=Decimal("0"))
    total_expense = sum((Decimal(r.amount) for r in all_records if r.type == "expense"), start=Decimal("0"))
    net_balance = total_income - total_expense

    def _money(value: Decimal) -> float:
        return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    category_map: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    monthly_income: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    monthly_expense: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for record in all_records:
        month_key = record.date.strftime("%Y-%m")
        if record.type == "income":
            monthly_income[month_key] += Decimal(record.amount)
        else:
            monthly_expense[month_key] += Decimal(record.amount)
            category_map[record.category] += Decimal(record.amount)

    expense_by_category = [
        {"category": category, "amount": _money(amount)}
        for category, amount in sorted(category_map.items(), key=lambda item: (-item[1], item[0]))
    ]

    all_months = sorted(set(monthly_income) | set(monthly_expense))
    monthly_trend = [
        {
            "month": month,
            "income": _money(monthly_income.get(month, Decimal("0"))),
            "expense": _money(monthly_expense.get(month, Decimal("0"))),
        }
        for month in all_months[-6:]
    ]

    budget_status = build_budget_status(db, current_user.id)
    over_budget = [
        {
            "category": item["category"],
            "limit": float(item["monthly_limit"]),
            "spent": float(item["current_spent"]),
            "over": _money(Decimal(item["current_spent"]) - Decimal(item["monthly_limit"])),
        }
        for item in budget_status
        if item["over_budget"]
    ]

    return {
        "total_income": _money(total_income),
        "total_expense": _money(total_expense),
        "net_balance": _money(net_balance),
        "expense_by_category": expense_by_category,
        "monthly_trend": monthly_trend,
        "over_budget": over_budget,
        "summary_scope": {
            "totals": "all_time",
            "over_budget": "current_month",
        },
    }
