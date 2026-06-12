from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from models.expense import ExpenseORM
from services.budget_summary import build_budget_status, build_budget_summary


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
    today = date.today()
    current_month_key = today.strftime("%Y-%m")
    
    # Load all records for trend and recent transactions
    all_records = db.query(ExpenseORM).filter(ExpenseORM.user_id == user_id).order_by(ExpenseORM.date.desc(), ExpenseORM.id.desc()).all()
    
    # Calculate monthly totals (current month)
    monthly_income = Decimal("0")
    monthly_expense = Decimal("0")
    category_map: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    
    # Trend data (last 6 months)
    trend_income = defaultdict(lambda: Decimal("0"))
    trend_expense = defaultdict(lambda: Decimal("0"))
    
    for record in all_records:
        month_key = record.date.strftime("%Y-%m")
        
        # Current month totals
        if month_key == current_month_key:
            if record.type == "income":
                monthly_income += Decimal(record.amount)
            else:
                monthly_expense += Decimal(record.amount)
                category_map[record.category] += Decimal(record.amount)
        
        # Trend data
        if record.type == "income":
            trend_income[month_key] += Decimal(record.amount)
        else:
            trend_expense[month_key] += Decimal(record.amount)

    # Monthly Balance
    monthly_balance = monthly_income - monthly_expense
    
    # Top Expense Category (current month)
    top_category = None
    if category_map:
        top_category = max(category_map.items(), key=lambda x: x[1])[0]
    
    # Monthly Trend (last 6 months, including empty months)
    monthly_trend = []
    for i in range(5, -1, -1):
        # Calculate month key for i months ago
        # Simplified month subtraction
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        m_key = f"{year:04d}-{month:02d}"
        
        monthly_trend.append({
            "month": m_key,
            "income": _money(trend_income.get(m_key, Decimal("0"))),
            "expense": _money(trend_expense.get(m_key, Decimal("0")))
        })
    
    # Expense by Category (current month)
    expense_by_category = [
        {"category": cat, "amount": _money(amt)}
        for cat, amt in sorted(category_map.items(), key=lambda x: (-x[1], x[0]))
    ]
    
    # Recent Transactions (last 10)
    recent_transactions = [
        {
            "date": r.date.strftime("%Y-%m-%d"),
            "category": r.category,
            "type": r.type,
            "amount": _money(Decimal(r.amount))
        }
        for r in all_records[:10]
    ]

    # Budget Integration
    budget_summary = build_budget_summary(db, user_id, current_month_key)
    
    over_count = sum(1 for item in budget_summary["items"] if item["status"] == "over")
    warning_count = sum(1 for item in budget_summary["items"] if item["status"] == "warning")
    budget_items = [
        {
            "category": item["category"],
            "amount": float(item["budget"]),
            "used": float(item["used"]),
            "remaining": float(item["remaining"]),
            "usagePercent": float(item["usageRate"]),
            "status": item["status"],
            "overBudget": bool(item["over_budget"]),
            "warning": bool(item["warning"]),
        }
        for item in budget_summary["items"]
    ]

    return {
        "monthlyIncome": _money(monthly_income),
        "monthlyExpense": _money(monthly_expense),
        "monthlyBalance": _money(monthly_balance),
        "topExpenseCategory": top_category,
        "monthlyTrend": monthly_trend,
        "expenseByCategory": expense_by_category,
        "recentTransactions": recent_transactions,
        # New Budget Info
        "totalBudget": budget_summary["totalBudget"],
        "totalUsed": budget_summary["totalUsed"],
        "totalRemaining": budget_summary["totalRemaining"],
        "budgetOverCount": over_count,
        "budgetWarningCount": warning_count,
        "budgetItems": budget_items,
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
            "amount": float(item["amount"]),
            "currentSpent": float(item["current_spent"]),
            "usagePercent": float(item["percent_used"]),
            "status": "over" if item["over_budget"] else ("warning" if item["warning"] else "safe"),
            "overBudget": bool(item["over_budget"]),
            "warning": bool(item["warning"]),
        }
        for item in budget_status
    ]

    return {
        "monthly_expense_trend": monthly_expense_trend,
        "category_distribution": category_distribution,
        "net_income_trend": net_income_trend,
        "budget_usage": budget_usage,
    }
