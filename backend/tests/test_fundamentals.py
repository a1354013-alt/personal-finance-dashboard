from __future__ import annotations

import time
from datetime import date
from decimal import Decimal

import pytest

from app.jobs.job_runner import JOB_TYPE_SYNC_FUNDAMENTALS
from models.job import SyncJobORM
from providers.fundamentals.base import BaseFundamentalsProvider, FundamentalsFetchResult, FundamentalsProviderError
from providers.fundamentals.factory import reset_fundamentals_provider_cache
from providers.fundamentals.timeout_wrapper import TimeoutFundamentalsProvider
from tests.conftest import auth_headers, drain_jobs, register_and_login


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


def test_fundamentals_sync_queues_job_then_filter_reads_db(client, monkeypatch: pytest.MonkeyPatch):
    provider = StaticProvider()
    reset_fundamentals_provider_cache()

    import app.jobs.job_runner as job_runner
    import services.fundamentals_service as fundamentals_service
    import routers.stocks as stocks_router

    monkeypatch.setattr(fundamentals_service, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(job_runner, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(stocks_router.StockDataService, "fetch_stock_info", classmethod(lambda cls, code: {"shortName": code}))
    monkeypatch.setattr(
        stocks_router.StockDataService,
        "fetch_price_history",
        classmethod(
            lambda cls, code: [{
                "stock_code": code,
                "trade_date": date(2026, 4, 10),
                "open": 99.0,
                "high": 101.0,
                "low": 98.0,
                "close": 100.0,
                "volume": 12345,
            }]
        ),
    )

    token = register_and_login(client, "fundamentals-ok@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})

    sync = client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})
    assert sync.status_code == 200
    snapshot = sync.json()[0]
    assert snapshot["stock_code"] == "AAPL"
    assert snapshot["status"] == "pending"

    drain_jobs()

    results = client.get("/api/stocks/filter", headers=auth_headers(token))
    assert results.status_code == 200
    payload = results.json()[0]
    assert payload["stock_code"] == "AAPL"
    assert payload["fundamentals"]["source"] == "test-static"
    assert payload["meta"]["status"] == "success"
    assert payload["meta"]["is_stale"] is False


def test_fundamentals_sync_failure_is_persisted_after_worker_runs(client, monkeypatch: pytest.MonkeyPatch):
    provider = StaticProvider(fail=True)
    reset_fundamentals_provider_cache()

    import app.jobs.job_runner as job_runner
    import services.fundamentals_service as fundamentals_service
    import routers.stocks as stocks_router

    monkeypatch.setattr(fundamentals_service, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(job_runner, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(stocks_router.StockDataService, "fetch_stock_info", classmethod(lambda cls, code: {"shortName": code}))
    monkeypatch.setattr(
        stocks_router.StockDataService,
        "fetch_price_history",
        classmethod(
            lambda cls, code: [{
                "stock_code": code,
                "trade_date": date(2026, 4, 10),
                "open": 99.0,
                "high": 101.0,
                "low": 98.0,
                "close": 100.0,
                "volume": 12345,
            }]
        ),
    )

    token = register_and_login(client, "fundamentals-fail@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})

    sync = client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})
    assert sync.status_code == 200
    assert sync.json()[0]["status"] == "pending"

    drain_jobs()

    results = client.get("/api/stocks/filter", headers=auth_headers(token))
    assert results.status_code == 200
    payload = results.json()[0]
    assert payload["passed"] is False
    assert any("status is 'failed'" in reason for reason in payload["fail_reasons"])


def test_get_watchlist_fundamentals_empty_when_no_watchlist(client):
    token = register_and_login(client, "fundamentals-list-empty@example.com")
    resp = client.get("/api/stocks/fundamentals", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_watchlist_fundamentals_empty_when_not_synced(client):
    token = register_and_login(client, "fundamentals-list-nosync@example.com")
    add = client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})
    assert add.status_code == 201

    resp = client.get("/api/stocks/fundamentals", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_job_rows_are_created_for_fundamentals_sync(client, monkeypatch: pytest.MonkeyPatch):
    provider = StaticProvider()
    reset_fundamentals_provider_cache()

    from db.database import SessionLocal

    import services.fundamentals_service as fundamentals_service
    import app.jobs.job_runner as job_runner
    import routers.stocks as stocks_router

    monkeypatch.setattr(fundamentals_service, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(job_runner, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(stocks_router.StockDataService, "fetch_stock_info", classmethod(lambda cls, code: {"shortName": code}))
    monkeypatch.setattr(
        stocks_router.StockDataService,
        "fetch_price_history",
        classmethod(
            lambda cls, code: [{
                "stock_code": code,
                "trade_date": date(2026, 4, 10),
                "open": 99.0,
                "high": 101.0,
                "low": 98.0,
                "close": 100.0,
                "volume": 12345,
            }]
        ),
    )

    token = register_and_login(client, "fundamentals-jobs@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})
    client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})

    with SessionLocal() as db:
        jobs = db.query(SyncJobORM).filter(SyncJobORM.job_type == JOB_TYPE_SYNC_FUNDAMENTALS).all()
        assert len(jobs) == 1
        assert jobs[0].status in {"pending", "success", "retrying", "running"}


def test_fundamentals_sync_reuses_active_job_for_same_user_and_stock(client, monkeypatch: pytest.MonkeyPatch):
    provider = StaticProvider()
    reset_fundamentals_provider_cache()

    from db.database import SessionLocal

    import app.jobs.job_runner as job_runner
    import routers.stocks as stocks_router
    import services.fundamentals_service as fundamentals_service

    monkeypatch.setattr(fundamentals_service, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(job_runner, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(stocks_router.StockDataService, "fetch_stock_info", classmethod(lambda cls, code: {"shortName": code}))
    monkeypatch.setattr(
        stocks_router.StockDataService,
        "fetch_price_history",
        classmethod(
            lambda cls, code: [{
                "stock_code": code,
                "trade_date": date(2026, 4, 10),
                "open": 99.0,
                "high": 101.0,
                "low": 98.0,
                "close": 100.0,
                "volume": 12345,
            }]
        ),
    )

    token = register_and_login(client, "fundamentals-dedupe@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})

    first = client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})
    second = client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})

    assert first.status_code == 200
    assert second.status_code == 200

    with SessionLocal() as db:
        jobs = db.query(SyncJobORM).filter(SyncJobORM.job_type == JOB_TYPE_SYNC_FUNDAMENTALS).all()
        assert len(jobs) == 1


def test_fundamentals_sync_allows_new_job_after_completion_and_for_other_users(client, monkeypatch: pytest.MonkeyPatch):
    provider = StaticProvider()
    reset_fundamentals_provider_cache()

    from db.database import SessionLocal

    import app.jobs.job_runner as job_runner
    import routers.stocks as stocks_router
    import services.fundamentals_service as fundamentals_service

    monkeypatch.setattr(fundamentals_service, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(job_runner, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(stocks_router.StockDataService, "fetch_stock_info", classmethod(lambda cls, code: {"shortName": code}))
    monkeypatch.setattr(
        stocks_router.StockDataService,
        "fetch_price_history",
        classmethod(
            lambda cls, code: [{
                "stock_code": code,
                "trade_date": date(2026, 4, 10),
                "open": 99.0,
                "high": 101.0,
                "low": 98.0,
                "close": 100.0,
                "volume": 12345,
            }]
        ),
    )

    token_a = register_and_login(client, "fundamentals-user-a@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token_a), json={"stock_code": "AAPL"})
    client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token_a), json={"force": True})
    drain_jobs()
    client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token_a), json={"force": True})

    token_b = register_and_login(client, "fundamentals-user-b@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token_b), json={"stock_code": "AAPL"})
    client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token_b), json={"force": True})

    with SessionLocal() as db:
        jobs = db.query(SyncJobORM).filter(SyncJobORM.job_type == JOB_TYPE_SYNC_FUNDAMENTALS).order_by(SyncJobORM.id.asc()).all()
        assert len(jobs) == 3
        assert '"user_id": 1' in jobs[0].payload
        assert '"user_id": 1' in jobs[1].payload
        assert '"user_id": 2' in jobs[2].payload
