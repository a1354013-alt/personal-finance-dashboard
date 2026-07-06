from __future__ import annotations

from datetime import date

import pytest

from db.database import SessionLocal
from models.stock import WatchlistORM
from providers.stock_price.base import StockQuote
from services.watchlist_service import sync_stock_price


def test_sync_stock_price_requires_watchlist_item():
    with pytest.raises(TypeError):
        sync_stock_price(None, stock_code="AAPL")  # type: ignore[arg-type]


def register_and_login(client, email: str) -> str:
    register_response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert register_response.status_code == 201
    login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_stock_sync_status_is_scoped_to_current_user_watchlist_item(client, monkeypatch):
    from app.jobs import get_job_runner

    class FakeProvider:
        name = "fake"

        def normalize_symbol(self, stock_code: str) -> str:
            return stock_code.strip().upper()

        def infer_market(self, _stock_code: str) -> tuple[str, str | None, str]:
            return "US", None, "USD"

        def fetch_quote(self, stock_code: str):
            return StockQuote(
                stock_code=stock_code,
                name="Scoped Inc",
                market="US",
                exchange=None,
                currency="USD",
                trade_date=date(2026, 5, 15),
                open=10,
                high=11,
                low=9,
                close=10.5,
                previous_close=10,
                volume=1000,
                provider=self.name,
            )

    monkeypatch.setattr("services.watchlist_service.get_stock_price_provider", lambda: FakeProvider())
    monkeypatch.setattr("services.stock_data_service.get_stock_price_provider", lambda: FakeProvider())

    token_a = register_and_login(client, "watch-user-a@example.com")
    token_b = register_and_login(client, "watch-user-b@example.com")

    add_a = client.post("/api/stocks/watchlist", headers=auth_headers(token_a), json={"stock_code": "AAPL"})
    add_b = client.post("/api/stocks/watchlist", headers=auth_headers(token_b), json={"stock_code": "AAPL"})
    assert add_a.status_code == 201
    assert add_b.status_code == 201

    runner = get_job_runner()
    assert runner.drain_once() is True

    with SessionLocal() as db:
        item_a = db.query(WatchlistORM).filter(WatchlistORM.id == add_a.json()["id"]).first()
        item_b = db.query(WatchlistORM).filter(WatchlistORM.id == add_b.json()["id"]).first()
        assert item_a.price_sync_status == "success"
        assert item_a.name == "Scoped Inc"
        assert item_b.price_sync_status == "pending"
        assert item_b.name is None


def test_watchlist_response_includes_currency(client, monkeypatch):
    from app.jobs import get_job_runner

    class FakeProvider:
        name = "fake"

        def normalize_symbol(self, stock_code: str) -> str:
            return stock_code.strip().upper()

        def infer_market(self, _stock_code: str) -> tuple[str, str | None, str]:
            return "US", None, "USD"

        def fetch_quote(self, stock_code: str):
            return StockQuote(
                stock_code=stock_code,
                name="Apple",
                market="US",
                exchange=None,
                currency="USD",
                trade_date=date(2026, 5, 15),
                open=10,
                high=11,
                low=9,
                close=10.5,
                previous_close=10,
                volume=1000,
                provider=self.name,
            )

    monkeypatch.setattr("services.watchlist_service.get_stock_price_provider", lambda: FakeProvider())
    monkeypatch.setattr("services.stock_data_service.get_stock_price_provider", lambda: FakeProvider())

    token = register_and_login(client, "watch-currency@example.com")
    add = client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})
    assert add.status_code == 201

    runner = get_job_runner()
    assert runner.drain_once() is True

    watchlist = client.get("/api/stocks/watchlist", headers=auth_headers(token))
    assert watchlist.status_code == 200
    assert watchlist.json()[0]["currency"] == "USD"

