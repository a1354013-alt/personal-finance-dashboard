from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_serializer, field_validator
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from db.database import Base


class BudgetORM(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=False)
    monthly_limit = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("UserORM", back_populates="budgets")

    __table_args__ = (UniqueConstraint("user_id", "category", name="_user_budget_category_uc"),)


class BudgetBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    monthly_limit: Decimal = Field(..., gt=0)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.strip()


class BudgetCreate(BudgetBase):
    pass


class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    created_at: datetime
    percent_used: Optional[float] = 0.0
    current_spent: Optional[Decimal] = Decimal("0.0")

    model_config = {"from_attributes": True}

    @field_serializer("monthly_limit", "current_spent")
    def serialize_decimals(self, value: Decimal) -> float:
        return float(value)
