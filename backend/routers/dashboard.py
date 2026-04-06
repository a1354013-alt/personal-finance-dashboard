"""
儀表板統計路由 - /api/dashboard (v0.6.0)
提供使用者個人財務數據統計。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import defaultdict
from datetime import datetime

from db.database import get_db
from models.expense import ExpenseORM
from models.user import UserORM
from models.budget import BudgetORM
from services.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """
    回傳當前使用者 Dashboard 所需的彙整資料，包含預算超支檢查。
    """
    # 只查詢該使用者的資料
    all_records = db.query(ExpenseORM).filter(ExpenseORM.user_id == current_user.id).all()

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
        for m in all_months[-6:]
    ]

    # 預算超支檢查 (v0.6.0)
    budgets = db.query(BudgetORM).filter(BudgetORM.user_id == current_user.id).all()
    over_budget_categories = []
    
    now = datetime.now()
    first_day = datetime(now.year, now.month, 1).date()

    for b in budgets:
        # 取得該類別當月總支出
        spent = sum(r.amount for r in all_records if (
            r.category == b.category and 
            r.type == "expense" and 
            r.date >= first_day
        ))
        
        if spent > b.monthly_limit:
            over_budget_categories.append({
                "category": b.category,
                "limit": b.monthly_limit,
                "spent": spent,
                "over": round(spent - b.monthly_limit, 2)
            })

    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_balance": round(net_balance, 2),
        "expense_by_category": expense_by_category,
        "monthly_trend": monthly_trend,
        "over_budget": over_budget_categories
    }
