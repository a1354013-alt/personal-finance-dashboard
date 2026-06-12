from __future__ import annotations

from datetime import date

import pytest

from db.database import SessionLocal
from models.stock import WatchlistORM
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
    from services.stock_data_service import StockDataService

    monkeypatch.setattr(
        StockDataService,
        "fetch_price_history",
        staticmethod(
            lambda stock_code: [
                {
                    "stock_code": stock_code,
                    "trade_date": date(2026, 5, 15),
                    "open": 10,
                    "high": 11,
                    "low": 9,
                    "close": 10.5,
                    "volume": 1000,
                }
            ]
        ),
    )
    monkeypatch.setattr(StockDataService, "fetch_stock_info", staticmethod(lambda _stock_code: {"shortName": "Scoped Inc"}))

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

