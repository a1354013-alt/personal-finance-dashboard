from __future__ import annotations

from datetime import date as DateType, datetime, timezone
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, field_serializer, field_validator
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from db.database import Base


class WatchlistORM(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=True)
    price_sync_status = Column(String(20), nullable=False, default="pending")
    last_sync_error = Column(Text, nullable=True)
    last_sync_attempt_at = Column(DateTime, nullable=True)

    user = relationship("UserORM", back_populates="watchlist")

    __table_args__ = (UniqueConstraint("user_id", "stock_code", name="_user_stock_uc"),)


class StockPriceORM(Base):
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
    status: Literal["pending", "success", "failed"]
    provider: str
    as_of_date: Optional[DateType] = None
    last_attempt_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WatchlistItemResponse(BaseModel):
    id: int
    user_id: int
    stock_code: str
    name: Optional[str] = None
    price: Optional[Decimal] = None
    date: Optional[DateType] = None
    volume: Optional[int] = None
    price_sync_status: str = "pending"
    last_sync_error: Optional[str] = None
    last_sync_attempt_at: Optional[datetime] = None
    price_sync: Optional[PriceSyncMeta] = None

    model_config = {"from_attributes": True}

    @field_serializer("price")
    def serialize_price(self, value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value)


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
