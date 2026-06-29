from __future__ import annotations

import pytest

from providers.yfinance_client import get_yfinance
from services.stock_data_service import StockDataService


def test_get_yfinance_reports_clear_install_message(monkeypatch: pytest.MonkeyPatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yfinance":
            raise ImportError("missing for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="Install backend requirements first"):
        get_yfinance()


def test_stock_data_service_handles_missing_yfinance_gracefully(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("services.stock_data_service.get_yfinance", lambda: (_ for _ in ()).throw(RuntimeError("Install backend requirements first")))

    assert StockDataService.fetch_real_price("AAPL") is None
    assert StockDataService.fetch_stock_info("AAPL") is None
    assert StockDataService.fetch_price_history("AAPL") == []
