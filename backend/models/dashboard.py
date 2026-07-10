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


class DashboardForecast(BaseModel):
    projectedIncome: float
    projectedExpense: float
    projectedBalance: float
    actualIncomeToDate: float
    actualExpenseToDate: float
    recurringIncomePending: float
    recurringExpensePending: float
    forecastWarnings: list[str] = Field(default_factory=list)


class DashboardUnbudgetedSpendingItem(BaseModel):
    category: str
    amount: float
    transactionCount: int


class DashboardSummaryResponse(BaseModel):
    monthlyIncome: float
    monthlyExpense: float
    monthlyBalance: float
    topExpenseCategory: Optional[str]
    monthlyTrend: list[DashboardMonthlyTrendItem] = Field(default_factory=list)
    expenseByCategory: list[DashboardExpenseByCategory] = Field(default_factory=list)
    recentTransactions: list[DashboardRecentTransaction] = Field(default_factory=list)
    totalBudget: float
    totalUsed: float
    totalRemaining: float
    budgetOverCount: int
    budgetWarningCount: int
    budgetItems: list["DashboardBudgetSummaryItem"] = Field(default_factory=list)
    monthlyForecast: DashboardForecast
    unbudgetedSpending: list[DashboardUnbudgetedSpendingItem] = Field(default_factory=list)


class DashboardBudgetUsageItem(BaseModel):
    category: str
    amount: float
    currentSpent: float
    usagePercent: float
    status: str
    overBudget: bool
    warning: bool


class DashboardBudgetSummaryItem(BaseModel):
    category: str
    amount: float
    used: float
    remaining: float
    usagePercent: float
    status: str
    overBudget: bool
    warning: bool


class DashboardChartsResponse(BaseModel):
    monthly_expense_trend: list[DashboardMonthlyTrendItem] = Field(default_factory=list)
    category_distribution: list[DashboardExpenseByCategory] = Field(default_factory=list)
    net_income_trend: list[DashboardMonthlyTrendItem] = Field(default_factory=list)
    budget_usage: list[DashboardBudgetUsageItem] = Field(default_factory=list)

