from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from models.fundamentals import FundamentalsSnapshot


class FundamentalsStatusMeta(BaseModel):
    provider: str
    ttl_hours: int
    is_stale: bool
    fetched_at: Optional[datetime] = None
    as_of_date: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None


class StockFundamentalsFilterResult(BaseModel):
    stock_code: str
    passed: bool
    fail_reasons: list[str]
    fundamentals: Optional[FundamentalsSnapshot] = None
    meta: FundamentalsStatusMeta


class FilterMetadataResponse(BaseModel):
    fundamentals_provider: str
    ttl_hours: int
    timeout_seconds: float
    message: str = Field(..., description="User-facing note about source and sync expectations.")

