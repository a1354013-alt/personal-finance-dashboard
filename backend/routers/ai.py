"""
AI 摘要路由
  - /api/ai/summary        財務摘要
  - /api/ai/stock-explain  股票篩選結果解說
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator, Field # 點 2: 匯入 validator, Field
from collections import defaultdict

from db.database import get_db
from models.expense import ExpenseORM
from services.ai_summary import generate_finance_summary, generate_stock_explanation
from services.stock_filter import evaluate_stock

router = APIRouter(prefix="/api/ai", tags=["AI"])


# ── /api/ai/summary ──────────────────────────────────────────────────────────

@router.get("/summary")
def ai_finance_summary(db: Session = Depends(get_db)):
    """
    根據資料庫中的記帳資料自動生成財務摘要文字。
    """
    records = db.query(ExpenseORM).all()
    
    # 點 8: 當無任何 expense 資料時直接回傳提示訊息
    if not records:
        return {"summary": "目前尚無財務資料，請先新增收入或支出記錄以生成財務摘要。"}

    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")

    # 找最高支出類別
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


# ── /api/ai/stock-explain ────────────────────────────────────────────────────

class StockExplainRequest(BaseModel):
    # 點 2: 對 stock_code 加入驗證
    stock_code: str = Field(..., description="股票代碼")
    net_income: float
    free_cash_flow: float
    revenue_growth: float

    @validator('stock_code')
    def stock_code_must_not_be_empty(cls, v):
        stripped = v.strip()
        if not stripped:
            raise ValueError('股票代碼不可為空')
        if len(stripped) > 20:
            raise ValueError('股票代碼長度過長')
        return stripped


@router.post("/stock-explain")
def ai_stock_explain(payload: StockExplainRequest):
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
