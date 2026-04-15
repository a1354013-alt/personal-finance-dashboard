from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_serializer, field_validator
from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint, Index

from db.database import Base


class FundamentalsORM(Base):
    __tablename__ = "fundamentals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, index=True)

    pe_ratio = Column(Numeric(18, 6), nullable=True)
    pb_ratio = Column(Numeric(18, 6), nullable=True)
    dividend_yield = Column(Numeric(18, 6), nullable=True)
    revenue_growth = Column(Numeric(18, 6), nullable=True)
    eps = Column(Numeric(18, 6), nullable=True)

    source = Column(String(50), nullable=False)
    as_of_date = Column(Date, nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("stock_code", "source", "as_of_date", name="_fundamentals_code_source_asof_uc"),
        Index("ix_fundamentals_stock_code_fetched_at", "stock_code", "fetched_at"),
    )


class FundamentalsBase(BaseModel):
    stock_code: str = Field(..., min_length=1, max_length=20)

    @field_validator("stock_code")
    @classmethod
    def normalize_stock_code(cls, value: str) -> str:
        return value.strip().upper()


class FundamentalsSnapshot(BaseModel):
    stock_code: str
    pe_ratio: Optional[Decimal] = None
    pb_ratio: Optional[Decimal] = None
    dividend_yield: Optional[Decimal] = None
    revenue_growth: Optional[Decimal] = None
    eps: Optional[Decimal] = None

    source: str
    as_of_date: date
    fetched_at: datetime
    status: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_serializer("pe_ratio", "pb_ratio", "dividend_yield", "revenue_growth", "eps")
    def serialize_optional_decimal(self, value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value)


class FundamentalsSyncRequest(FundamentalsBase):
    force: bool = False


class FundamentalsSyncOptions(BaseModel):
    force: bool = False


class FundamentalsSyncResponse(BaseModel):
    stock_code: str
    queued: bool
    message: str
