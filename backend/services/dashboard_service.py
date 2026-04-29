from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from models.expense import ExpenseORM
from services.budget_summary import build_budget_status


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _load_expense_aggregates(*, db: Session, user_id: int) -> tuple[list[ExpenseORM], dict[str, Decimal], dict[str, Decimal], dict[str, Decimal]]:
    all_records = db.query(ExpenseORM).filter(ExpenseORM.user_id == user_id).all()
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
    return all_records, category_map, monthly_income, monthly_expense


def build_dashboard_summary(*, db: Session, user_id: int) -> dict:
    all_records, category_map, monthly_income, monthly_expense = _load_expense_aggregates(db=db, user_id=user_id)

    total_income = sum((Decimal(r.amount) for r in all_records if r.type == "income"), start=Decimal("0"))
    total_expense = sum((Decimal(r.amount) for r in all_records if r.type == "expense"), start=Decimal("0"))
    net_balance = total_income - total_expense

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

    budget_status = build_budget_status(db, user_id)
    over_budget = [
        {
            "category": item["category"],
            "limit": float(item["monthly_limit"]),
            "spent": float(item["current_spent"]),
            "over": _money(Decimal(item["current_spent"]) - Decimal(item["monthly_limit"])),
        }
        for item in budget_status
        if Decimal(item["current_spent"]) > Decimal(item["monthly_limit"])
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


def build_dashboard_charts(*, db: Session, user_id: int) -> dict:
    _, category_map, monthly_income, monthly_expense = _load_expense_aggregates(db=db, user_id=user_id)
    months = sorted(set(monthly_income) | set(monthly_expense))[-12:]
    budget_status = build_budget_status(db, user_id)

    monthly_expense_trend = [
        {"month": month, "income": 0.0, "expense": _money(monthly_expense.get(month, Decimal("0")))}
        for month in months
    ]
    net_income_trend = [
        {
            "month": month,
            "income": _money(monthly_income.get(month, Decimal("0"))),
            "expense": _money(monthly_expense.get(month, Decimal("0"))),
        }
        for month in months
    ]
    category_distribution = [
        {"category": category, "amount": _money(amount)}
        for category, amount in sorted(category_map.items(), key=lambda item: (-item[1], item[0]))
    ]
    budget_usage = [
        {
            "category": item["category"],
            "monthly_limit": float(item["monthly_limit"]),
            "current_spent": float(item["current_spent"]),
            "percent_used": float(item["percent_used"]),
        }
        for item in budget_status
    ]

    return {
        "monthly_expense_trend": monthly_expense_trend,
        "category_distribution": category_distribution,
        "net_income_trend": net_income_trend,
        "budget_usage": budget_usage,
    }

