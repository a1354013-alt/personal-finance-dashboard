from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import date

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENV", "development")

from app.jobs import get_job_runner  # noqa: E402
from db.database import engine, init_db, reset_sqlite_db  # noqa: E402
from main import app as fastapi_app, rate_limiter  # noqa: E402
from providers.stock_price.base import StockQuote  # noqa: E402


class FakeStockPriceProvider:
    name = "fake-stock-price"

    def __init__(self) -> None:
        self.quotes: dict[str, StockQuote | None] = {}
        self.default_quote = StockQuote(
            stock_code="AAPL",
            name="Fake Stock",
            market="US",
            exchange=None,
            currency="USD",
            trade_date=date(2026, 4, 10),
            open=99.0,
            high=101.0,
            low=98.0,
            close=100.0,
            previous_close=99.0,
            volume=12345,
            provider=self.name,
        )

    def normalize_symbol(self, stock_code: str) -> str:
        code = stock_code.strip().upper()
        if code.isdigit() and len(code) == 4:
            return f"{code}.TW"
        return code

    def infer_market(self, stock_code: str) -> tuple[str, str | None, str]:
        normalized = self.normalize_symbol(stock_code)
        if normalized.endswith(".TW"):
            return "Taiwan", "TWSE", "TWD"
        if normalized.endswith(".TWO"):
            return "Taiwan", "TPEx", "TWD"
        return "US", None, "USD"

    def set_quote(self, quote: StockQuote | None) -> None:
        if quote is None:
            self.quotes["*"] = None
            return
        self.quotes[quote.stock_code] = quote

    def fetch_quote(self, stock_code: str) -> StockQuote | None:
        normalized = self.normalize_symbol(stock_code)
        if "*" in self.quotes:
            return self.quotes["*"]
        quote = self.quotes.get(normalized)
        if quote is not None:
            return quote
        market, exchange, currency = self.infer_market(normalized)
        return StockQuote(
            stock_code=normalized,
            name=normalized,
            market=market,
            exchange=exchange,
            currency=currency,
            trade_date=self.default_quote.trade_date,
            open=self.default_quote.open,
            high=self.default_quote.high,
            low=self.default_quote.low,
            close=self.default_quote.close,
            previous_close=self.default_quote.previous_close,
            volume=self.default_quote.volume,
            provider=self.name,
        )


@pytest.fixture(autouse=True)
def fake_stock_price_provider(monkeypatch):
    provider = FakeStockPriceProvider()
    monkeypatch.setattr("services.watchlist_service.get_stock_price_provider", lambda: provider)
    monkeypatch.setattr("services.stock_data_service.get_stock_price_provider", lambda: provider)
    return provider


@pytest.fixture(autouse=True)
def clean_db():
    runner = get_job_runner()
    while runner.drain_once():
        pass
    reset_sqlite_db()
    init_db()
    rate_limiter._windows.clear()
    yield
    rate_limiter._windows.clear()
    while runner.drain_once():
        pass
    reset_sqlite_db()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(fastapi_app)


def register_and_login(client: TestClient, email: str) -> str:
    register_response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert register_response.status_code == 201

    login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def drain_jobs(max_cycles: int = 20) -> None:
    runner = get_job_runner()
    for _ in range(max_cycles):
        processed = runner.drain_once()
        if not processed:
            break

