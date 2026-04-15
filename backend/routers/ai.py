from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.ai import (
    AIProviderMeta,
    BudgetAdviceResponse,
    FinanceSummaryResponse,
    StockExplainRequest,
    StockExplainResponse,
)
from models.expense import ExpenseORM
from models.user import UserORM
from services.auth import get_current_user
from services.ai_service import AIInsightsService
from services.budget_summary import build_budget_status
from services.stock_filter import evaluate_stock
from providers.llm import get_llm_provider

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.get("/summary", response_model=FinanceSummaryResponse)
def ai_finance_summary(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    records = db.query(ExpenseORM).filter(ExpenseORM.user_id == current_user.id).all()
    if not records:
        return FinanceSummaryResponse(
            summary="No records yet. Add income and expenses to generate an AI summary.",
            meta=AIProviderMeta(provider="fallback", is_fallback=True, error=None),
        )

    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")

    category_map: dict[str, float] = defaultdict(float)
    for record in records:
        if record.type == "expense":
            category_map[record.category] += record.amount

    top_category = max(category_map, key=category_map.get) if category_map else "N/A"
    service = AIInsightsService(get_llm_provider())
    result = service.finance_summary(
        total_income=float(total_income),
        total_expense=float(total_expense),
        top_category=top_category,
        period="all_time",
    )
    return FinanceSummaryResponse(
        summary=result.text,
        meta=AIProviderMeta(provider=result.provider, is_fallback=result.is_fallback, error=result.error),
    )


@router.post("/stock-explain", response_model=StockExplainResponse)
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
    service = AIInsightsService(get_llm_provider())
    metrics = {
        "net_income": payload.net_income,
        "free_cash_flow": payload.free_cash_flow,
        "revenue_growth": payload.revenue_growth,
    }
    ai_result = service.stock_explanation(
        stock_code=payload.stock_code,
        passed=bool(result["passed"]),
        fail_reasons=list(result["fail_reasons"]),
        metrics=metrics,
    )
    return StockExplainResponse(
        stock_code=result["stock_code"],
        passed=bool(result["passed"]),
        fail_reasons=list(result["fail_reasons"]),
        explanation=ai_result.text,
        metrics=metrics,
        meta=AIProviderMeta(provider=ai_result.provider, is_fallback=ai_result.is_fallback, error=ai_result.error),
    )


@router.get("/budget-advice", response_model=BudgetAdviceResponse)
def get_budget_advice_api(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    budget_status = build_budget_status(db, current_user.id)
    service = AIInsightsService(get_llm_provider())
    result = service.budget_advice(budget_status=budget_status)
    return BudgetAdviceResponse(
        budget_status=budget_status,
        advice=result.text,
        meta=AIProviderMeta(provider=result.provider, is_fallback=result.is_fallback, error=result.error),
    )
