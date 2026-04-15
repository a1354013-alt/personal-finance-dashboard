from __future__ import annotations

import os
from functools import lru_cache

from .base import BaseFundamentalsProvider
from .timeout_wrapper import TimeoutFundamentalsProvider
from .yfinance_provider import YFinanceFundamentalsProvider


@lru_cache(maxsize=1)
def get_fundamentals_provider() -> BaseFundamentalsProvider:
    name = os.getenv("FUNDAMENTALS_PROVIDER", "yfinance").strip().lower()

    if name in {"yfinance", "yf"}:
        return TimeoutFundamentalsProvider(YFinanceFundamentalsProvider())

    # Unknown provider -> default to yfinance (still wrapped with timeout)
    return TimeoutFundamentalsProvider(YFinanceFundamentalsProvider())


def reset_fundamentals_provider_cache() -> None:
    get_fundamentals_provider.cache_clear()

