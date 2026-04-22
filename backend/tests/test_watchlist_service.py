from __future__ import annotations

import pytest

from services.watchlist_service import sync_stock_price


def test_sync_stock_price_requires_watchlist_item():
    with pytest.raises(TypeError):
        sync_stock_price(None, stock_code="AAPL")  # type: ignore[arg-type]

