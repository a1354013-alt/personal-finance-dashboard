from __future__ import annotations

import logging
from typing import Any, Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class StockDataService:
    @staticmethod
    def _format_stock_code(stock_code: str) -> str:
        code = stock_code.strip().upper()
        if code.isdigit() and len(code) == 4:
            return f"{code}.TW"
        return code

    @classmethod
    def fetch_real_price(cls, stock_code: str) -> Optional[dict[str, Any]]:
        formatted_code = cls._format_stock_code(stock_code)
        try:
            ticker = yf.Ticker(formatted_code)
            history = ticker.history(period="5d", auto_adjust=False)

            if history.empty:
                logger.warning("No price history returned for %s", formatted_code)
                return None

            last_row = history.iloc[-1]
            close_price = last_row.get("Close")
            if close_price is None:
                logger.warning("Missing close price for %s", formatted_code)
                return None

            trade_date = last_row.name.strftime("%Y-%m-%d")
            return {
                "stock_code": formatted_code,
                "trade_date": trade_date,
                "open": float(last_row["Open"]) if "Open" in last_row else None,
                "high": float(last_row["High"]) if "High" in last_row else None,
                "low": float(last_row["Low"]) if "Low" in last_row else None,
                "close": float(close_price),
                "volume": float(last_row["Volume"]) if "Volume" in last_row else None,
            }
        except Exception:
            logger.exception("Failed to fetch price for %s", formatted_code)
            return None

    @classmethod
    def fetch_stock_info(cls, stock_code: str) -> Optional[dict[str, Any]]:
        formatted_code = cls._format_stock_code(stock_code)
        try:
            ticker = yf.Ticker(formatted_code)
            info = getattr(ticker, "info", None)
            if not info or len(info) <= 1:
                logger.warning("No stock info returned for %s", formatted_code)
                return None
            return info
        except Exception:
            logger.exception("Failed to fetch stock info for %s", formatted_code)
            return None
