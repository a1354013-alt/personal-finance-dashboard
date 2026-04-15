from __future__ import annotations

from decimal import Decimal

import yfinance as yf

from .base import BaseFundamentalsProvider, FundamentalsFetchResult, FundamentalsProviderError


class YFinanceFundamentalsProvider(BaseFundamentalsProvider):
    """Fetch fundamentals via yfinance.

    Notes:
    - yfinance scrapes Yahoo Finance (not an official market data API).
    - Returned fields vary by symbol and market.
    - This provider should be wrapped with a timeout guard to avoid hanging API calls.
    """

    name = "yfinance"

    def fetch(self, *, stock_code: str) -> FundamentalsFetchResult:
        try:
            ticker = yf.Ticker(stock_code)
            info = getattr(ticker, "info", None) or {}
        except Exception as exc:
            raise FundamentalsProviderError(f"yfinance failed for {stock_code}: {exc}") from exc

        def as_decimal(value) -> Decimal | None:
            if value is None:
                return None
            try:
                return Decimal(str(value))
            except Exception:
                return None

        pe_ratio = as_decimal(info.get("trailingPE") or info.get("forwardPE"))
        pb_ratio = as_decimal(info.get("priceToBook"))

        # Yahoo dividendYield is typically a fraction (e.g. 0.0123). Store as percentage (1.23).
        dividend_raw = info.get("dividendYield")
        dividend_yield = None
        if dividend_raw is not None:
            dividend_dec = as_decimal(dividend_raw)
            if dividend_dec is not None:
                dividend_yield = dividend_dec * Decimal("100")

        # revenueGrowth is typically a fraction (e.g. 0.05). Store as percentage (5.0).
        growth_raw = info.get("revenueGrowth")
        revenue_growth = None
        if growth_raw is not None:
            growth_dec = as_decimal(growth_raw)
            if growth_dec is not None:
                revenue_growth = growth_dec * Decimal("100")

        eps = as_decimal(info.get("trailingEps"))

        return FundamentalsFetchResult(
            stock_code=stock_code,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            dividend_yield=dividend_yield,
            revenue_growth=revenue_growth,
            eps=eps,
            source=self.name,
        )

