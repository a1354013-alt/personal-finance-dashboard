"""
記帳系統資料模型
"""
from sqlalchemy import Column, Integer, Float, String, Date, Text
from sqlalchemy.sql import func
from db.database import Base
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date


# ── SQLAlchemy ORM 模型 ──────────────────────────────────────────────────────

class ExpenseORM(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)   # "income" | "expense"
    date = Column(String(20), nullable=False)   # ISO 格式 YYYY-MM-DD
    note = Column(Text, nullable=True)


# ── Pydantic Schema ──────────────────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    amount: float
    category: str
    type: str       # "income" | "expense"
    date: str       # YYYY-MM-DD
    note: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("income", "expense"):
            raise ValueError("type 必須為 'income' 或 'expense'")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount 必須大於 0")
        return v


class ExpenseResponse(BaseModel):
    id: int
    amount: float
    category: str
    type: str
    date: str
    note: Optional[str] = None

    model_config = {"from_attributes": True}
