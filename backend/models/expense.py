"""
記帳系統資料模型
"""
from sqlalchemy import Column, Integer, Float, String, Date, Text
from db.database import Base
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date  # 點 1: 匯入 date 型別


# ── SQLAlchemy ORM 模型 (點 1: date 改為 Date 型別) ──────────────────────────

class ExpenseORM(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)   # "income" | "expense"
    date = Column(Date, nullable=False)         # 點 1: 修正為 Date 型別
    note = Column(Text, nullable=True)


# ── Pydantic Schema (點 1, 2: 修正型別與補強驗證) ───────────────────────────

class ExpenseCreate(BaseModel):
    amount: float
    category: str
    type: str       # "income" | "expense"
    date: date      # 點 1: 修正為 date 型別，Pydantic 自動驗證格式
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

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        # 點 2: 禁止空字串與僅空白字元
        if not v or not v.strip():
            raise ValueError("category 不能為空或僅包含空白")
        return v.strip()


class ExpenseResponse(BaseModel):
    id: int
    amount: float
    category: str
    type: str
    date: date      # 點 1: 修正為 date 型別
    note: Optional[str] = None

    model_config = {"from_attributes": True}
