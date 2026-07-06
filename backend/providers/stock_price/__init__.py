from __future__ import annotations

from providers.stock_price.yfinance_provider import YFinanceStockPriceProvider

_provider = YFinanceStockPriceProvider()


def get_stock_price_provider() -> YFinanceStockPriceProvider:
    return _provider
