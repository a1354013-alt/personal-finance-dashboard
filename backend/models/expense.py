"""
記帳資料模型
定義 Expense ORM 模型與 Pydantic Schemas。
"""
from sqlalchemy import Column, Integer, Float, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date


# ── SQLAlchemy ORM 模型 ──────────────────────────────────────────────────────

class ExpenseORM(Base):
    """記帳資料表"""
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)   # "income" | "expense"
    date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)

    # 建立與使用者的關聯
    user = relationship("UserORM", back_populates="expenses")


# ── Pydantic Schemas (用於 API 驗證與回傳) ───────────────────────────────────

class ExpenseCreate(BaseModel):
    amount: float
    category: str
    type: str       # "income" | "expense"
    date: date
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
        if not v or not v.strip():
            raise ValueError("category 不能為空或僅包含空白")
        return v.strip()


class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    category: str
    type: str
    date: date
    note: Optional[str] = None

    model_config = {"from_attributes": True}
