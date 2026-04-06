"""
股票資料模型
包含自選股 (Watchlist) 與市場價格歷史 (StockPrice)。
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from db.database import Base


# ── SQLAlchemy ORM 模型 ──────────────────────────────────────────────────────

class WatchlistORM(Base):
    """使用者自選股清單"""
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=True)
    
    # 建立與使用者的關聯
    user = relationship("UserORM", back_populates="watchlist")

    # 限制同一使用者不可重複加入相同股票
    __table_args__ = (UniqueConstraint('user_id', 'stock_code', name='_user_stock_uc'),)


class StockPriceORM(Base):
    """市場價格歷史資料"""
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(String(20), nullable=False) # 使用 YYYY-MM-DD 字串
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 確保同一股票同一天的資料唯一
    __table_args__ = (UniqueConstraint('stock_code', 'trade_date', name='_stock_date_uc'),)


# ── Pydantic Schemas (用於 API 驗證與回傳) ───────────────────────────────────

class WatchlistCreate(BaseModel):
    """建立自選股請求"""
    stock_code: str

    @field_validator('stock_code')
    @classmethod
    def validate_stock_code(cls, v):
        v = v.strip().upper()
        if not v:
            raise ValueError("股票代碼不可為空")
        if len(v) > 20:
            raise ValueError("股票代碼長度不可超過 20 字元")
        return v


class WatchlistItemResponse(BaseModel):
    """自選股回應"""
    id: int
    user_id: int
    stock_code: str
    name: Optional[str] = None
    # 擴充欄位：用於前端顯示最新價格資訊
    price: Optional[float] = None
    date: Optional[str] = None
    volume: Optional[float] = None
    # 新增欄位：標示價格同步狀態
    price_sync_status: Optional[str] = "success"

    model_config = {"from_attributes": True}


class StockFilterRequest(BaseModel):
    """股票篩選引擎輸入資料"""
    stock_code: str
    net_income: float
    free_cash_flow: float
    revenue_growth: float
    extra: Optional[dict] = None


class StockFilterResult(BaseModel):
    """股票篩選引擎輸出結果"""
    stock_code: str
    passed: bool
    fail_reasons: List[str]
