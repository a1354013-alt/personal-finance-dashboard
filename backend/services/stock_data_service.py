from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any, Optional

from providers.yfinance_client import get_yfinance
from providers.stock_price import get_stock_price_provider
logger = logging.getLogger(__name__)


class StockDataService:
    @staticmethod
    def provider_name() -> str:
        return get_stock_price_provider().name

    @staticmethod
    def infer_currency(stock_code: str, info: Optional[dict[str, Any]] = None) -> str | None:
        raw = None
        if info:
            raw = info.get("currency") or info.get("financialCurrency")
        if raw:
            currency = str(raw).strip().upper()
            if currency:
                return currency

        normalized_code = StockDataService.normalize_stock_code(stock_code)
        if normalized_code.endswith(".TW") or normalized_code.endswith(".TWO"):
            return "TWD"
        if normalized_code:
            return "USD"
        return None

    @staticmethod
    def normalize_stock_code(stock_code: str) -> str:
        return get_stock_price_provider().normalize_symbol(stock_code)

    @classmethod
    def fetch_real_price(cls, stock_code: str) -> Optional[dict[str, Any]]:
        formatted_code = cls.normalize_stock_code(stock_code)
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

            trade_date = date.fromisoformat(last_row.name.strftime("%Y-%m-%d"))
            return {
                "stock_code": formatted_code,
                "trade_date": trade_date,
                "open": float(last_row["Open"]) if "Open" in last_row else None,
                "high": float(last_row["High"]) if "High" in last_row else None,
                "low": float(last_row["Low"]) if "Low" in last_row else None,
                "close": float(close_price),
                "volume": int(last_row["Volume"]) if "Volume" in last_row and last_row["Volume"] is not None else None,
            }
        except Exception:
            logger.exception("Failed to fetch price for %s", formatted_code)
            return None

    @classmethod
    def fetch_stock_info(cls, stock_code: str) -> Optional[dict[str, Any]]:
        formatted_code = cls.normalize_stock_code(stock_code)
        try:
            yf = get_yfinance()
            ticker = yf.Ticker(formatted_code)
            info = getattr(ticker, "info", None)
            if not info or len(info) <= 1:
                logger.warning("No stock info returned for %s", formatted_code)
                return None
            return info
        except Exception:
            logger.exception("Failed to fetch stock info for %s", formatted_code)
            return None

    @classmethod
    def fetch_price_history(cls, stock_code: str, *, period: str = "6mo") -> list[dict[str, Any]]:
        formatted_code = cls.normalize_stock_code(stock_code)
        timeout = float(os.getenv("STOCK_DATA_TIMEOUT_SECONDS", "8"))
        try:
            yf = get_yfinance()
            ticker = yf.Ticker(formatted_code)
            history = ticker.history(period=period, auto_adjust=False, timeout=timeout)
            if history.empty:
                return []
            points: list[dict[str, Any]] = []
            for idx, row in history.iterrows():
                close_price = row.get("Close")
                if close_price is None:
                    continue
                points.append(
                    {
                        "stock_code": formatted_code,
                        "trade_date": date.fromisoformat(idx.strftime("%Y-%m-%d")),
                        "open": float(row["Open"]) if "Open" in row else None,
                        "high": float(row["High"]) if "High" in row else None,
                        "low": float(row["Low"]) if "Low" in row else None,
                        "close": float(close_price),
                        "volume": int(row["Volume"]) if "Volume" in row and row["Volume"] is not None else None,
                    }
                )
            return points
        except Exception:
            logger.exception("Failed to fetch price history for %s", formatted_code)
            return []
