from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from .base import BaseFundamentalsProvider, FundamentalsFetchResult, FundamentalsProviderError


class TimeoutFundamentalsProvider(BaseFundamentalsProvider):
    def __init__(self, inner: BaseFundamentalsProvider, *, timeout_seconds: float | None = None) -> None:
        self._inner = inner
        self.name = getattr(inner, "name", "provider")
        self._timeout = float(os.getenv("FUNDAMENTALS_TIMEOUT_SECONDS", timeout_seconds or 8.0))

    def fetch(self, *, stock_code: str) -> FundamentalsFetchResult:
        with ThreadPoolExecutor(max_workers=1) as executor:
            fut = executor.submit(self._inner.fetch, stock_code=stock_code)
            try:
                return fut.result(timeout=self._timeout)
            except FuturesTimeoutError as exc:
                raise FundamentalsProviderError(
                    f"Fundamentals fetch timed out after {self._timeout}s for {stock_code}."
                ) from exc

