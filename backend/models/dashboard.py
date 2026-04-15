from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DashboardExpenseByCategory(BaseModel):
    category: str
    amount: float


class DashboardMonthlyTrendItem(BaseModel):
    month: str = Field(..., description="YYYY-MM")
    income: float
    expense: float


class DashboardOverBudgetItem(BaseModel):
    category: str
    limit: float
    spent: float
    over: float


class DashboardSummaryScope(BaseModel):
    totals: Literal["all_time"]
    over_budget: Literal["current_month"]


class DashboardSummaryResponse(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    expense_by_category: list[DashboardExpenseByCategory]
    monthly_trend: list[DashboardMonthlyTrendItem]
    over_budget: list[DashboardOverBudgetItem]
    summary_scope: DashboardSummaryScope

