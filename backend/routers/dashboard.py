from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.expense import ExpenseORM
from models.user import UserORM
from services.auth import get_current_user
from services.budget_summary import build_budget_status

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    all_records = db.query(ExpenseORM).filter(ExpenseORM.user_id == current_user.id).all()

    total_income = round(sum(r.amount for r in all_records if r.type == "income"), 2)
    total_expense = round(sum(r.amount for r in all_records if r.type == "expense"), 2)
    net_balance = round(total_income - total_expense, 2)

    category_map: dict[str, float] = defaultdict(float)
    monthly_income: dict[str, float] = defaultdict(float)
    monthly_expense: dict[str, float] = defaultdict(float)

    for record in all_records:
        month_key = record.date.strftime("%Y-%m")
        if record.type == "income":
            monthly_income[month_key] += record.amount
        else:
            monthly_expense[month_key] += record.amount
            category_map[record.category] += record.amount

    expense_by_category = [
        {"category": category, "amount": round(amount, 2)}
        for category, amount in sorted(category_map.items(), key=lambda item: (-item[1], item[0]))
    ]

    all_months = sorted(set(monthly_income) | set(monthly_expense))
    monthly_trend = [
        {
            "month": month,
            "income": round(monthly_income.get(month, 0), 2),
            "expense": round(monthly_expense.get(month, 0), 2),
        }
        for month in all_months[-6:]
    ]

    budget_status = build_budget_status(db, current_user.id)
    over_budget = [
        {
            "category": item["category"],
            "limit": item["monthly_limit"],
            "spent": item["current_spent"],
            "over": round(item["current_spent"] - item["monthly_limit"], 2),
        }
        for item in budget_status
        if item["over_budget"]
    ]

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": net_balance,
        "expense_by_category": expense_by_category,
        "monthly_trend": monthly_trend,
        "over_budget": over_budget,
    }
