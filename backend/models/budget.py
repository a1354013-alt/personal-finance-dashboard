from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

class BudgetORM(Base):
    """預算資料模型 (v0.6.0)"""
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)
    monthly_limit = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 關聯
    user = relationship("UserORM", back_populates="budgets")

# Pydantic Models
class BudgetBase(BaseModel):
    category: str = Field(..., min_length=1)
    monthly_limit: float = Field(..., gt=0)

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    created_at: datetime
    percent_used: Optional[float] = 0.0  # 用於回傳目前使用率
    current_spent: Optional[float] = 0.0 # 目前已支出

    class Config:
        from_attributes = True
