from __future__ import annotations

from datetime import date as DateType, datetime, timezone
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_serializer, field_validator
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from db.database import Base
from models.ai import AIProviderMeta


class WatchlistORM(Base):
    # User-scoped: one watchlist row per (user_id, stock_code).
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=True)
    market = Column(String(50), nullable=True)
    exchange = Column(String(20), nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    last_price = Column(Numeric(18, 4), nullable=True)
    previous_close = Column(Numeric(18, 4), nullable=True)
    price_change = Column(Numeric(18, 4), nullable=True)
    change_percent = Column(Numeric(18, 6), nullable=True)
    volume = Column(BigInteger, nullable=True)
    provider = Column(String(50), nullable=True)
    price_updated_at = Column(DateTime, nullable=True)
    sync_status = Column(String(20), nullable=False, default="sync_required")
    sync_required = Column(Integer, nullable=False, default=1)
    sync_error = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_risk_notes = Column(Text, nullable=True)
    ai_updated_at = Column(DateTime, nullable=True)
    price_sync_status = Column(String(20), nullable=False, default="pending")
    last_sync_error = Column(Text, nullable=True)
    last_sync_attempt_at = Column(DateTime, nullable=True)

    user = relationship("UserORM", back_populates="watchlist")

    __table_args__ = (UniqueConstraint("user_id", "stock_code", name="_user_stock_uc"),)


class StockPriceORM(Base):
    # Shared cache: prices are stored per (stock_code, trade_date) and reused across users.
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4), nullable=True)
    high = Column(Numeric(18, 4), nullable=True)
    low = Column(Numeric(18, 4), nullable=True)
    close = Column(Numeric(18, 4), nullable=False)
    volume = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("stock_code", "trade_date", name="_stock_date_uc"),)


class StockPriceHistoryORM(Base):
    __tablename__ = "stock_price_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4), nullable=True)
    high = Column(Numeric(18, 4), nullable=True)
    low = Column(Numeric(18, 4), nullable=True)
    close = Column(Numeric(18, 4), nullable=False)
    volume = Column(BigInteger, nullable=True)
    source = Column(String(50), nullable=False, default="yfinance")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("stock_code", "trade_date", name="_stock_history_date_uc"),)


class WatchlistCreate(BaseModel):
    stock_code: str

    @field_validator("stock_code")
    @classmethod
    def validate_stock_code(cls, value: str) -> str:
        stock_code = value.strip().upper()
        if not stock_code:
            raise ValueError("Stock code is required.")
        if len(stock_code) > 20:
            raise ValueError("Stock code must be 20 characters or fewer.")
        return stock_code


class PriceSyncMeta(BaseModel):
    status: Literal["pending", "success", "failed", "ready", "sync_required", "sync_queued", "unsupported", "error"]
    provider: str
    as_of_date: Optional[DateType] = None
    last_attempt_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WatchlistItemResponse(BaseModel):
    id: int
    stock_code: str
    symbol: Optional[str] = None
    name: Optional[str] = None
    price: Optional[Decimal] = None
    currency: str = "USD"
    market: Optional[str] = None
    exchange: Optional[str] = None
    last_price: Optional[Decimal] = None
    previous_close: Optional[Decimal] = None
    price_change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    date: Optional[DateType] = None
    volume: Optional[int] = None
    provider: Optional[str] = None
    price_updated_at: Optional[datetime] = None
    sync_status: str = "sync_required"
    sync_required: bool = True
    sync_error: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_risk_notes: Optional[str] = None
    ai_updated_at: Optional[datetime] = None
    price_sync_status: str = "pending"
    last_sync_error: Optional[str] = None
    last_sync_attempt_at: Optional[datetime] = None
    price_sync: Optional[PriceSyncMeta] = None

    model_config = {"from_attributes": True}

    @field_serializer("price", "last_price", "previous_close", "price_change", "change_percent")
    def serialize_price(self, value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value)


class StockAIAnalysisResponse(BaseModel):
    status: Literal["ready", "sync_required", "unsupported", "error"]
    stock_code: str
    summary: Optional[str] = None
    recent_price_movement: Optional[str] = None
    volume_note: Optional[str] = None
    risk_notes: list[str] = Field(default_factory=list)
    watch_points: list[str] = Field(default_factory=list)
    disclaimer: str
    meta: Optional[AIProviderMeta] = None


class StockFilterRequest(BaseModel):
    stock_code: str
    net_income: float
    free_cash_flow: float
    revenue_growth: float
    extra: Optional[dict] = None


class StockFilterResult(BaseModel):
    stock_code: str
    passed: bool
    fail_reasons: list[str]


class StockPriceHistoryPoint(BaseModel):
    trade_date: DateType
    close: Decimal
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    volume: Optional[int] = None

    model_config = {"from_attributes": True}

    @field_serializer("close", "open", "high", "low")
    def serialize_optional_price(self, value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value)


class StockAIExplanationResponse(BaseModel):
    status: Literal["ready", "sync_required", "sync_queued", "unsupported"]
    stock_code: str
    message: Optional[str] = None
    explanation: Optional[str] = None
    can_sync: bool = False
    job_id: Optional[int] = None
    request_id: Optional[str] = None
    meta: Optional[AIProviderMeta] = None


class StockDashboardResponse(BaseModel):
    selected_stock_code: Optional[str] = None
    watchlist: list[WatchlistItemResponse]
    price_history: list[StockPriceHistoryPoint]
    fundamentals: Optional[dict] = None
    ai_explanation: Optional[StockAIExplanationResponse] = None
