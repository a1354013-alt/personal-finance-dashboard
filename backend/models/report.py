from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


MONTH_PATTERN = r"^\d{4}-\d{2}$"


class MonthlyReportQuery(BaseModel):
    month: str = Field(..., pattern=MONTH_PATTERN)
    format: str

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"csv", "pdf"}:
            raise ValueError("format must be either csv or pdf.")
        return normalized


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
