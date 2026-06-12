from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer, field_validator
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from db.database import Base
from models.month import MONTH_PATTERN


class BudgetORM(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    month = Column(String(7), nullable=False, index=True)  # YYYY-MM
    category = Column(String(50), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("UserORM", back_populates="budgets")

    __table_args__ = (UniqueConstraint("user_id", "month", "category", name="_user_month_category_uc"),)


class BudgetBase(BaseModel):
    month: str = Field(..., pattern=MONTH_PATTERN)
    category: str = Field(..., min_length=1, max_length=50)
    amount: Decimal = Field(..., ge=0)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        category = value.strip()
        if not category:
            raise ValueError("category is required.")
        return category


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    category: str | None = Field(None, min_length=1, max_length=50)
    amount: Decimal | None = Field(None, ge=0)


class BudgetItem(BaseModel):
    id: int
    category: str
    budget: float
    used: float
    remaining: float
    usageRate: float
    status: str
    over_budget: bool
    warning: bool


class BudgetSummaryResponse(BaseModel):
    month: str
    totalBudget: float
    totalUsed: float
    totalRemaining: float
    items: list[BudgetItem]


class BudgetResponse(BudgetBase):
    id: int
    percent_used: float = 0.0
    current_spent: Decimal = Decimal("0.0")
    over_budget: bool = False
    warning: bool = False

    model_config = {"from_attributes": True}

    @field_serializer("amount", "current_spent")
    def serialize_decimals(self, value: Decimal) -> float:
        return float(value)
