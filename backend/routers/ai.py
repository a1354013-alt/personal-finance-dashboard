from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from db.database import get_db
from models.expense import ExpenseORM
from models.user import UserORM
from services.ai_summary import (
    generate_budget_advice,
    generate_finance_summary,
    generate_stock_explanation,
)
from services.auth import get_current_user
from services.budget_summary import build_budget_status
from services.stock_filter import evaluate_stock

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.get("/summary")
def ai_finance_summary(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    records = db.query(ExpenseORM).filter(ExpenseORM.user_id == current_user.id).all()
    if not records:
        return {"summary": "No records yet. Add income and expenses to generate an AI summary."}

    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")

    category_map: dict[str, float] = defaultdict(float)
    for record in records:
        if record.type == "expense":
            category_map[record.category] += record.amount

    top_category = max(category_map, key=category_map.get) if category_map else "N/A"
    return {
        "summary": generate_finance_summary(
            total_income=total_income,
            total_expense=total_expense,
            top_category=top_category,
        )
    }


class StockExplainRequest(BaseModel):
    stock_code: str = Field(..., description="Stock code.")
    net_income: float
    free_cash_flow: float
    revenue_growth: float

    @field_validator("stock_code")
    @classmethod
    def validate_stock_code(cls, value: str) -> str:
        stock_code = value.strip()
        if not stock_code:
            raise ValueError("Stock code is required.")
        if len(stock_code) > 20:
            raise ValueError("Stock code is too long.")
        return stock_code


@router.post("/stock-explain")
def ai_stock_explain(
    payload: StockExplainRequest,
    current_user: UserORM = Depends(get_current_user),
):
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
    return {**result, "explanation": explanation}


@router.get("/budget-advice")
def get_budget_advice_api(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    budget_status = build_budget_status(db, current_user.id)
    advice = generate_budget_advice(budget_status)
    return {"budget_status": budget_status, "advice": advice}
