from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from models.budget import BudgetORM
from models.expense import ExpenseORM


def get_month_range_from_str(month_str: str) -> tuple[date, date]:
    """Given YYYY-MM, return (start_date, end_date) for filtering."""
    dt = datetime.strptime(month_str, "%Y-%m")
    start_date = dt.date().replace(day=1)
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)
    return start_date, end_date


def build_budget_summary(db: Session, user_id: int, month: str) -> dict:
    start_date, end_date = get_month_range_from_str(month)
    
    # Get all expenses for the user in the given month
    expenses = (
        db.query(ExpenseORM)
        .filter(
            ExpenseORM.user_id == user_id,
            ExpenseORM.type == "expense",
            ExpenseORM.date >= start_date,
            ExpenseORM.date < end_date,
        )
        .all()
    )
    
    spend_by_category = defaultdict(Decimal)
    for exp in expenses:
        spend_by_category[exp.category] += Decimal(str(exp.amount))
        
    # Get all budgets for the user in the given month
    budgets = (
        db.query(BudgetORM)
        .filter(BudgetORM.user_id == user_id, BudgetORM.month == month)
        .all()
    )
    
    total_budget = Decimal("0")
    total_used = Decimal("0")
    items = []
    
    # Track which categories have budgets to identify expenses without budgets later if needed
    # But requirement says "items" based on budgets.
    
    for b in budgets:
        cat = b.category
        budget_amt = Decimal(str(b.amount))
        used_amt = spend_by_category.get(cat, Decimal("0"))
        remaining = budget_amt - used_amt
        usage_rate = (float(used_amt) / float(budget_amt) * 100) if budget_amt > 0 else (100.0 if used_amt > 0 else 0.0)
        
        status = "safe"
        if usage_rate > 100:
            status = "over"
        elif usage_rate >= 80:
            status = "warning"
        over_budget = usage_rate > 100
        warning = 80 <= usage_rate <= 100
            
        items.append({
            "id": b.id,
            "category": cat,
            "budget": float(budget_amt),
            "used": float(used_amt),
            "remaining": float(remaining),
            "usageRate": round(usage_rate, 1),
            "status": status,
            "over_budget": over_budget,
            "warning": warning,
        })
        
        total_budget += budget_amt
        total_used += used_amt
        
    return {
        "month": month,
        "totalBudget": float(total_budget),
        "totalUsed": float(total_used),
        "totalRemaining": float(total_budget - total_used),
        "items": sorted(items, key=lambda x: x["usageRate"], reverse=True)
    }


def build_budget_status(db: Session, user_id: int, month: str | None = None) -> list[dict]:
    """Legacy compatibility or simple list view."""
    if not month:
        month = date.today().strftime("%Y-%m")
        
    summary = build_budget_summary(db, user_id, month)
    
    # Map summary items back to the format expected by BudgetResponse if needed,
    # but we'll likely update the router to use the new summary.
    res = []
    for item in summary["items"]:
        res.append({
            "id": item.get("id"),
            "month": month,
            "category": item["category"],
            "amount": item["budget"],
            "current_spent": item["used"],
            "percent_used": item["usageRate"],
            "over_budget": item["over_budget"],
            "warning": item["warning"],
        })
    return res
