from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from models.fundamentals import FundamentalsORM
from services.fundamentals_service import STATUS_SUCCESS, is_stale


@dataclass(frozen=True)
class FundamentalsScreenResult:
    stock_code: str
    passed: bool
    fail_reasons: list[str]


def screen_fundamentals(row: FundamentalsORM | None) -> FundamentalsScreenResult:
    if row is None:
        return FundamentalsScreenResult(stock_code="UNKNOWN", passed=False, fail_reasons=["No fundamentals cached yet."])

    reasons: list[str] = []
    if row.status != STATUS_SUCCESS:
        reasons.append(f"Fundamentals status is '{row.status}'.")
        if row.error_message:
            reasons.append(f"Provider error: {row.error_message}")
        return FundamentalsScreenResult(stock_code=row.stock_code, passed=False, fail_reasons=reasons)

    if is_stale(fetched_at=row.fetched_at):
        reasons.append("Fundamentals data is stale. Sync to refresh.")

    # Simple baseline screen rules (documented in README):
    # - EPS > 0
    # - P/E between 0 and 25
    # - P/B between 0 and 5
    # - Revenue growth >= 0%
    # - Dividend yield >= 0% (does not require dividends)
    pe = _to_decimal(row.pe_ratio)
    pb = _to_decimal(row.pb_ratio)
    eps = _to_decimal(row.eps)
    rev = _to_decimal(row.revenue_growth)
    div = _to_decimal(row.dividend_yield)

    if eps is None or eps <= 0:
        reasons.append("EPS must be positive.")
    if pe is None or pe <= 0 or pe > 25:
        reasons.append("P/E must be in (0, 25].")
    if pb is None or pb <= 0 or pb > 5:
        reasons.append("P/B must be in (0, 5].")
    if rev is None or rev < 0:
        reasons.append("Revenue growth must be >= 0%.")
    if div is None or div < 0:
        reasons.append("Dividend yield must be >= 0%.")

    return FundamentalsScreenResult(stock_code=row.stock_code, passed=len(reasons) == 0, fail_reasons=reasons)


def _to_decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value)
    except Exception:
        return None

