from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from models.month import MONTH_PATTERN


class MonthlyReportBudgetItem(BaseModel):
    category: str
    amount: float
    used: float
    remaining: float
    usagePercent: float
    status: str


class MonthlyReportTransactionItem(BaseModel):
    date: str
    category: str
    type: str
    amount: float
    note: str = ""


class MonthlyReportPayload(BaseModel):
    month: str = Field(..., pattern=MONTH_PATTERN)
    exportedAt: datetime
    monthlyIncome: float
    monthlyExpense: float
    monthlyBalance: float
    expenseByCategory: list[dict[str, float | str]] = Field(default_factory=list)
    budgetItems: list[MonthlyReportBudgetItem] = Field(default_factory=list)
    recentTransactions: list[MonthlyReportTransactionItem] = Field(default_factory=list)
    disclaimer: str
