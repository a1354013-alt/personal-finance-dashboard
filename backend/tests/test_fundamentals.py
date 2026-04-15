from __future__ import annotations

import time
from datetime import date
from decimal import Decimal

import pytest

from providers.fundamentals.base import BaseFundamentalsProvider, FundamentalsFetchResult, FundamentalsProviderError
from providers.fundamentals.timeout_wrapper import TimeoutFundamentalsProvider
from providers.fundamentals.factory import reset_fundamentals_provider_cache


def register_and_login(client, email: str) -> str:
    register_response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert register_response.status_code == 201
    login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class StaticProvider(BaseFundamentalsProvider):
    name = "test-static"

    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail

    def fetch(self, *, stock_code: str) -> FundamentalsFetchResult:
        if self._fail:
            raise FundamentalsProviderError("upstream failed")
        return FundamentalsFetchResult(
            stock_code=stock_code,
            pe_ratio=Decimal("10"),
            pb_ratio=Decimal("2"),
            dividend_yield=Decimal("1.5"),
            revenue_growth=Decimal("5"),
            eps=Decimal("3"),
            source=self.name,
        )


class SlowProvider(BaseFundamentalsProvider):
    name = "test-slow"

    def fetch(self, *, stock_code: str) -> FundamentalsFetchResult:
        time.sleep(0.2)
        return FundamentalsFetchResult(
            stock_code=stock_code,
            pe_ratio=None,
            pb_ratio=None,
            dividend_yield=None,
            revenue_growth=None,
            eps=None,
            source=self.name,
        )


def test_fundamentals_timeout_wrapper(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FUNDAMENTALS_TIMEOUT_SECONDS", "0.01")
    provider = TimeoutFundamentalsProvider(SlowProvider())
    with pytest.raises(FundamentalsProviderError):
        provider.fetch(stock_code="AAPL")


def test_fundamentals_sync_success_and_filter_reads_db(client, monkeypatch: pytest.MonkeyPatch):
    provider = StaticProvider()
    reset_fundamentals_provider_cache()

    import routers.stocks as stocks_router

    monkeypatch.setattr(stocks_router, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(
        stocks_router.StockDataService, "fetch_stock_info", classmethod(lambda cls, code: {"shortName": code})
    )
    monkeypatch.setattr(stocks_router.StockDataService, "fetch_real_price", classmethod(lambda cls, code: None))

    token = register_and_login(client, "fundamentals-ok@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})

    sync = client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})
    assert sync.status_code == 200
    snapshot = sync.json()[0]
    assert snapshot["stock_code"] == "AAPL"
    assert snapshot["status"] == "success"
    assert snapshot["source"] == "test-static"

    results = client.get("/api/stocks/filter", headers=auth_headers(token))
    assert results.status_code == 200
    payload = results.json()[0]
    assert payload["stock_code"] == "AAPL"
    assert payload["fundamentals"]["source"] == "test-static"
    assert payload["meta"]["status"] == "success"
    assert payload["meta"]["is_stale"] is False


def test_fundamentals_sync_failure_is_persisted(client, monkeypatch: pytest.MonkeyPatch):
    provider = StaticProvider(fail=True)
    reset_fundamentals_provider_cache()

    import routers.stocks as stocks_router

    monkeypatch.setattr(stocks_router, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(
        stocks_router.StockDataService, "fetch_stock_info", classmethod(lambda cls, code: {"shortName": code})
    )
    monkeypatch.setattr(stocks_router.StockDataService, "fetch_real_price", classmethod(lambda cls, code: None))

    token = register_and_login(client, "fundamentals-fail@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})

    sync = client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})
    assert sync.status_code == 200
    snapshot = sync.json()[0]
    assert snapshot["status"] == "failed"
    assert snapshot["error_message"]

    results = client.get("/api/stocks/filter", headers=auth_headers(token))
    assert results.status_code == 200
    payload = results.json()[0]
    assert payload["passed"] is False
    assert any("status is 'failed'" in reason for reason in payload["fail_reasons"])
