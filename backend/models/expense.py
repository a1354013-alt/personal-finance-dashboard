from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from db.database import Base


class ExpenseORM(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)
    date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)

    user = relationship("UserORM", back_populates="expenses")


class ExpenseCreate(BaseModel):
    amount: float
    category: str
    type: str
    date: date
    note: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in {"income", "expense"}:
            raise ValueError("type must be either 'income' or 'expense'.")
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("amount must be greater than 0.")
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        category = value.strip()
        if not category:
            raise ValueError("category is required.")
        if len(category) > 50:
            raise ValueError("category must be 50 characters or fewer.")
        return category

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        note = value.strip()
        return note or None


class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    category: str
    type: str
    date: date
    note: Optional[str] = None

    model_config = {"from_attributes": True}
