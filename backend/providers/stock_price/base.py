from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class StockQuote:
    stock_code: str
    name: str | None
    market: str
    exchange: str | None
    currency: str
    trade_date: date
    open: float | None
    high: float | None
    low: float | None
    close: float
    previous_close: float | None
    volume: int | None
    provider: str


class StockPriceProvider(Protocol):
    name: str

    def normalize_symbol(self, stock_code: str) -> str:
        ...

    def infer_market(self, stock_code: str) -> tuple[str, str | None, str]:
        ...

    def fetch_quote(self, stock_code: str) -> StockQuote | None:
        ...
