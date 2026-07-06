from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.jobs.job_runner import JOB_TYPE_SYNC_FUNDAMENTALS, JOB_TYPE_SYNC_STOCK_MARKET_DATA
from db.database import SessionLocal
from models.job import JOB_STATUS_FAILED, JOB_STATUS_SUCCESS, SyncJobORM
from models.stock import WatchlistORM
from providers.fundamentals.base import BaseFundamentalsProvider, FundamentalsFetchResult, FundamentalsProviderError
from providers.fundamentals.factory import reset_fundamentals_provider_cache
from providers.stock_price.base import StockQuote
from tests.conftest import auth_headers, drain_jobs, register_and_login


class FlakyProvider(BaseFundamentalsProvider):
    name = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, *, stock_code: str) -> FundamentalsFetchResult:
        self.calls += 1
        if self.calls < 3:
            raise FundamentalsProviderError("temporary upstream failure")
        return FundamentalsFetchResult(
            stock_code=stock_code,
            pe_ratio=Decimal("12"),
            pb_ratio=Decimal("3"),
            dividend_yield=Decimal("1.2"),
            revenue_growth=Decimal("8"),
            eps=Decimal("4"),
            source=self.name,
        )


class AlwaysFailProvider(BaseFundamentalsProvider):
    name = "always-fail"

    def fetch(self, *, stock_code: str) -> FundamentalsFetchResult:
        raise FundamentalsProviderError("hard failure")


def test_background_job_creation_retry_and_failure_recovery(client, monkeypatch):
    provider = FlakyProvider()
    reset_fundamentals_provider_cache()

    import app.jobs.job_runner as job_runner
    import services.fundamentals_service as fundamentals_service
    import routers.stocks as stocks_router

    monkeypatch.setattr(fundamentals_service, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(job_runner, "get_fundamentals_provider", lambda: provider)

    token = register_and_login(client, "jobs@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})
    response = client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})

    assert response.status_code == 200
    assert response.json()[0]["status"] == "pending"

    drain_jobs(max_cycles=10)

    with SessionLocal() as db:
      job = db.query(SyncJobORM).filter(SyncJobORM.job_type == JOB_TYPE_SYNC_FUNDAMENTALS).one()
      assert job.status == JOB_STATUS_SUCCESS
      assert job.attempts == 3


def test_background_job_marks_failed_after_max_retries(client, monkeypatch):
    provider = AlwaysFailProvider()
    reset_fundamentals_provider_cache()

    import app.jobs.job_runner as job_runner
    import services.fundamentals_service as fundamentals_service
    import routers.stocks as stocks_router

    monkeypatch.setattr(fundamentals_service, "get_fundamentals_provider", lambda: provider)
    monkeypatch.setattr(job_runner, "get_fundamentals_provider", lambda: provider)

    token = register_and_login(client, "jobs-fail@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})
    client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})

    drain_jobs(max_cycles=10)

    with SessionLocal() as db:
      job = db.query(SyncJobORM).filter(SyncJobORM.job_type == JOB_TYPE_SYNC_FUNDAMENTALS).one()
      assert job.status == JOB_STATUS_FAILED
      assert job.attempts == 3
      assert job.error_message


def test_stock_price_background_job_succeeds_with_fake_provider(client, fake_stock_price_provider):
    fake_stock_price_provider.set_quote(
        StockQuote(
            stock_code="2330.TW",
            name="TSMC",
            market="Taiwan",
            exchange="TWSE",
            currency="TWD",
            trade_date=date(2026, 7, 6),
            open=990,
            high=1005,
            low=980,
            close=1000,
            previous_close=950,
            volume=12345678,
            provider=fake_stock_price_provider.name,
        )
    )
    token = register_and_login(client, "stock-job-success@example.com")
    add = client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "2330"})
    assert add.status_code == 201

    drain_jobs(max_cycles=5)

    with SessionLocal() as db:
        job = db.query(SyncJobORM).filter(SyncJobORM.job_type == JOB_TYPE_SYNC_STOCK_MARKET_DATA).one()
        item = db.query(WatchlistORM).filter(WatchlistORM.id == add.json()["id"]).one()
        assert job.status == JOB_STATUS_SUCCESS
        assert item.price_sync_status == "success"
        assert item.sync_status == "ready"
        assert item.currency == "TWD"
        assert item.last_price == 1000


def test_stock_price_background_job_fails_with_fake_provider(client, fake_stock_price_provider):
    fake_stock_price_provider.set_quote(None)
    token = register_and_login(client, "stock-job-failure@example.com")
    add = client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "2330"})
    assert add.status_code == 201

    drain_jobs(max_cycles=5)

    with SessionLocal() as db:
        job = db.query(SyncJobORM).filter(SyncJobORM.job_type == JOB_TYPE_SYNC_STOCK_MARKET_DATA).one()
        item = db.query(WatchlistORM).filter(WatchlistORM.id == add.json()["id"]).one()
        assert job.status == JOB_STATUS_FAILED
        assert item.price_sync_status == "failed"
        assert item.sync_status == "error"
        assert item.sync_required == 1
        assert item.sync_error
