from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from models.budget import BudgetResponse


class AIProviderMeta(BaseModel):
    provider: str = Field(..., description="Provider that generated the output (after any fallback).")
    is_fallback: bool = Field(..., description="True when deterministic fallback was used.")
    error: Optional[str] = Field(None, description="Upstream provider error (if fallback was triggered).")


class FinanceSummaryResponse(BaseModel):
    summary: str
    meta: AIProviderMeta


class StockExplainRequest(BaseModel):
    stock_code: str = Field(..., description="Stock code.")
    net_income: float
    free_cash_flow: float
    revenue_growth: float

    @field_validator("stock_code")
    @classmethod
    def validate_stock_code(cls, value: str) -> str:
        stock_code = value.strip().upper()
        if not stock_code:
            raise ValueError("Stock code is required.")
        if len(stock_code) > 20:
            raise ValueError("Stock code is too long.")
        return stock_code


class StockExplainResponse(BaseModel):
    stock_code: str
    passed: bool
    fail_reasons: list[str]
    explanation: str
    meta: AIProviderMeta
    metrics: dict[str, Any] = Field(default_factory=dict)


class BudgetAdviceResponse(BaseModel):
    budget_status: list[BudgetResponse]
    advice: str
    meta: AIProviderMeta
