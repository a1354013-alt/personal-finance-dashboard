"""
Dashboard 摘要路由 - /api/dashboard/summary
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import defaultdict

from db.database import get_db
from models.expense import ExpenseORM

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """
    回傳 Dashboard 所需的彙整資料。
    """
    # 全部記錄
    all_records = db.query(ExpenseORM).all()

    total_income = sum(r.amount for r in all_records if r.type == "income")
    total_expense = sum(r.amount for r in all_records if r.type == "expense")
    net_balance = total_income - total_expense

    # 各類別支出
    category_map: dict = defaultdict(float)
    for r in all_records:
        if r.type == "expense":
            category_map[r.category] += r.amount
    expense_by_category = [
        {"category": k, "amount": round(v, 2)}
        for k, v in sorted(category_map.items(), key=lambda x: -x[1])
    ]

    # 每月趨勢
    monthly_income: dict = defaultdict(float)
    monthly_expense: dict = defaultdict(float)
    for r in all_records:
        # r.date 是 date 物件，取前 7 碼 YYYY-MM
        month_key = r.date.strftime("%Y-%m")
        if r.type == "income":
            monthly_income[month_key] += r.amount
        else:
            monthly_expense[month_key] += r.amount

    all_months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))
    monthly_trend = [
        {
            "month": m,
            "income": round(monthly_income.get(m, 0), 2),
            "expense": round(monthly_expense.get(m, 0), 2),
        }
        for m in all_months[-6:]  # 最近 6 個月
    ]

    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_balance": round(net_balance, 2),
        "expense_by_category": expense_by_category,
        "monthly_trend": monthly_trend,
    }
