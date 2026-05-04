from __future__ import annotations

from typing import Literal, Optional

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


class DashboardRecentTransaction(BaseModel):
    date: str
    category: str
    type: str
    amount: float


class DashboardSummaryResponse(BaseModel):
    monthlyIncome: float
    monthlyExpense: float
    monthlyBalance: float
    topExpenseCategory: Optional[str]
    monthlyTrend: list[DashboardMonthlyTrendItem]
    expenseByCategory: list[DashboardExpenseByCategory]
    recentTransactions: list[DashboardRecentTransaction]


class DashboardBudgetUsageItem(BaseModel):
    category: str
    monthly_limit: float
    current_spent: float
    percent_used: float


class DashboardChartsResponse(BaseModel):
    monthly_expense_trend: list[DashboardMonthlyTrendItem]
    category_distribution: list[DashboardExpenseByCategory]
    net_income_trend: list[DashboardMonthlyTrendItem]
    budget_usage: list[DashboardBudgetUsageItem]

