"""
股票模組資料模型
"""
from sqlalchemy import Column, Integer, Float, String
from db.database import Base
from pydantic import BaseModel
from typing import Optional, List


# ── SQLAlchemy ORM 模型 ──────────────────────────────────────────────────────

class WatchlistORM(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=True)
    price = Column(Float, nullable=True)
    date = Column(String(20), nullable=True)


# ── Pydantic Schema ──────────────────────────────────────────────────────────

class WatchlistItemResponse(BaseModel):
    id: int
    stock_code: str
    name: Optional[str] = None
    price: Optional[float] = None
    date: Optional[str] = None

    model_config = {"from_attributes": True}


class StockFilterRequest(BaseModel):
    """股票篩選引擎輸入資料"""
    stock_code: str
    net_income: float
    free_cash_flow: float
    revenue_growth: float   # 百分比，例如 5.0 代表 5%
    extra: Optional[dict] = None


class StockFilterResult(BaseModel):
    """股票篩選引擎輸出結果"""
    stock_code: str
    passed: bool
    fail_reasons: List[str]
