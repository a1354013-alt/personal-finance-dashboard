"""
AI 摘要路由 - /api/ai
提供財務摘要、股票分析解說與預算建議。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, Field
from collections import defaultdict
from datetime import datetime

from db.database import get_db
from models.expense import ExpenseORM
from models.budget import BudgetORM
from models.user import UserORM
from services.auth import get_current_user
from services.ai_summary import (
    generate_finance_summary, 
    generate_stock_explanation,
    generate_budget_advice
)
from services.stock_filter import evaluate_stock

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.get("/summary")
def ai_finance_summary(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
): # 確保用戶隔離
    """
    根據當前使用者的記帳資料自動生成財務摘要文字。
    """
    records = db.query(ExpenseORM).filter(ExpenseORM.user_id == current_user.id).all()
    
    if not records:
        return {"summary": "目前尚無財務資料，請先新增收入或支出記錄以生成財務摘要。"}

    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")

    category_map: dict = defaultdict(float)
    for r in records:
        if r.type == "expense":
            category_map[r.category] += r.amount
    top_category = max(category_map, key=category_map.get) if category_map else "無資料"

    summary = generate_finance_summary(
        total_income=total_income,
        total_expense=total_expense,
        top_category=top_category,
    )
    return {"summary": summary}


class StockExplainRequest(BaseModel):
    stock_code: str = Field(..., description="股票代碼")
    net_income: float
    free_cash_flow: float
    revenue_growth: float

    @field_validator('stock_code')
    @classmethod
    def stock_code_must_not_be_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('股票代碼不可為空')
        if len(stripped) > 20:
            raise ValueError('股票代碼長度過長')
        return stripped


@router.post("/stock-explain")
def ai_stock_explain(
    payload: StockExplainRequest,
    current_user: UserORM = Depends(get_current_user)
): # 確保用戶隔離
    """
    對指定股票基本面數據執行篩選並生成解說文字。
    """
    result = evaluate_stock(
        stock_code=payload.stock_code,
        net_income=payload.net_income,
        free_cash_flow=payload.free_cash_flow,
        revenue_growth=payload.revenue_growth,
    )
    explanation = generate_stock_explanation(
        stock_code=payload.stock_code,
        passed=result["passed"],
        fail_reasons=result["fail_reasons"],
        net_income=payload.net_income,
        free_cash_flow=payload.free_cash_flow,
        revenue_growth=payload.revenue_growth,
    )
    return {
        "stock_code": payload.stock_code,
        "passed": result["passed"],
        "fail_reasons": result["fail_reasons"],
        "explanation": explanation,
    }


@router.get("/budget-advice")
def get_budget_advice_api(
    db: Session = Depends(get_db), 
    current_user: UserORM = Depends(get_current_user)
): # 確保用戶隔離
    """獲取預算分析與 AI 建議"""
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1).date()
    
    budgets = db.query(BudgetORM).filter(BudgetORM.user_id == current_user.id).all()
    expenses = db.query(ExpenseORM).filter(
        ExpenseORM.user_id == current_user.id,
        ExpenseORM.date >= month_start,
        ExpenseORM.type == "expense"
    ).all()
    
    expense_map = defaultdict(float)
    for e in expenses:
        expense_map[e.category] += e.amount
        
    budget_status = []
    for b in budgets:
        spent = expense_map[b.category]
        percent = (spent / b.monthly_limit * 100) if b.monthly_limit > 0 else 0
        budget_status.append({
            "category": b.category,
            "monthly_limit": b.monthly_limit,
            "current_spent": spent,
            "percent_used": percent,
            "over_budget": spent > b.monthly_limit
        })
        
    advice = generate_budget_advice(budget_status)
    return {
        "budget_status": budget_status,
        "advice": advice
    }
