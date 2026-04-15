from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FundamentalsFetchResult:
    stock_code: str
    pe_ratio: Decimal | None
    pb_ratio: Decimal | None
    dividend_yield: Decimal | None
    revenue_growth: Decimal | None
    eps: Decimal | None
    source: str


class FundamentalsProviderError(RuntimeError):
    pass


class BaseFundamentalsProvider:
    name: str = "base"

    def fetch(self, *, stock_code: str) -> FundamentalsFetchResult:
        raise NotImplementedError

