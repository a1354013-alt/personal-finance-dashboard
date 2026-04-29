from __future__ import annotations

from decimal import Decimal

from app.jobs.job_runner import JOB_TYPE_SYNC_FUNDAMENTALS
from db.database import SessionLocal
from models.job import JOB_STATUS_FAILED, JOB_STATUS_SUCCESS, SyncJobORM
from providers.fundamentals.base import BaseFundamentalsProvider, FundamentalsFetchResult, FundamentalsProviderError
from providers.fundamentals.factory import reset_fundamentals_provider_cache
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

    import routers.stocks as stocks_router

    monkeypatch.setattr(stocks_router, "get_fundamentals_provider", lambda: provider)

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

    import routers.stocks as stocks_router

    monkeypatch.setattr(stocks_router, "get_fundamentals_provider", lambda: provider)

    token = register_and_login(client, "jobs-fail@example.com")
    client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})
    client.post("/api/stocks/fundamentals/sync", headers=auth_headers(token), json={"force": True})

    drain_jobs(max_cycles=10)

    with SessionLocal() as db:
      job = db.query(SyncJobORM).filter(SyncJobORM.job_type == JOB_TYPE_SYNC_FUNDAMENTALS).one()
      assert job.status == JOB_STATUS_FAILED
      assert job.attempts == 3
      assert job.error_message
