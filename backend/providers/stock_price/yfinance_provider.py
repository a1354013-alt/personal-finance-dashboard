from __future__ import annotations

import logging
import os
from datetime import date

from providers.stock_price.base import StockQuote
from providers.yfinance_client import get_yfinance

logger = logging.getLogger(__name__)


class YFinanceStockPriceProvider:
    name = "yfinance"

    def normalize_symbol(self, stock_code: str) -> str:
        code = stock_code.strip().upper()
        if code.isdigit() and len(code) == 4:
            return f"{code}.TW"
        return code

    def infer_market(self, stock_code: str) -> tuple[str, str | None, str]:
        normalized = self.normalize_symbol(stock_code)
        if normalized.endswith(".TW"):
            return "Taiwan", "TWSE", "TWD"
        if normalized.endswith(".TWO"):
            return "Taiwan", "TPEx", "TWD"
        return "US", None, "USD"

    def fetch_quote(self, stock_code: str) -> StockQuote | None:
        formatted_code = self.normalize_symbol(stock_code)
        market, exchange, fallback_currency = self.infer_market(formatted_code)
        timeout = float(os.getenv("STOCK_DATA_TIMEOUT_SECONDS", "8"))
        try:
            yf = get_yfinance()
            ticker = yf.Ticker(formatted_code)
            history = ticker.history(period="5d", auto_adjust=False, timeout=timeout)
            if history.empty:
                logger.warning("No price history returned for %s", formatted_code)
                return None

            last_row = history.iloc[-1]
            close_price = last_row.get("Close")
            if close_price is None:
                logger.warning("Missing close price for %s", formatted_code)
                return None

            previous_close = None
            if len(history.index) >= 2:
                previous_value = history.iloc[-2].get("Close")
                if previous_value is not None:
                    previous_close = float(previous_value)

            info = getattr(ticker, "info", None) or {}
            name = info.get("shortName") or info.get("longName")
            currency = str(info.get("currency") or info.get("financialCurrency") or fallback_currency).upper()

            return StockQuote(
                stock_code=formatted_code,
                name=str(name)[:100] if name else None,
                market=market,
                exchange=exchange,
                currency=currency,
                trade_date=date.fromisoformat(last_row.name.strftime("%Y-%m-%d")),
                open=float(last_row["Open"]) if "Open" in last_row else None,
                high=float(last_row["High"]) if "High" in last_row else None,
                low=float(last_row["Low"]) if "Low" in last_row else None,
                close=float(close_price),
                previous_close=previous_close,
                volume=int(last_row["Volume"]) if "Volume" in last_row and last_row["Volume"] is not None else None,
                provider=self.name,
            )
        except Exception:
            logger.exception("Failed to fetch quote for %s", formatted_code)
            return None
