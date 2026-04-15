from __future__ import annotations

from datetime import date

import pytest


def register_and_login(client, email: str) -> str:
    register_response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert register_response.status_code == 201
    login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_money_and_date_serialization_contracts(client, monkeypatch: pytest.MonkeyPatch):
    token = register_and_login(client, "contract@example.com")

    expense = client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 123.45, "category": "Food", "type": "expense", "date": "2026-04-10", "note": "Lunch"},
    )
    assert expense.status_code == 201
    payload = expense.json()
    assert isinstance(payload["amount"], (int, float))
    assert payload["date"] == "2026-04-10"

    import routers.stocks as stocks_router

    monkeypatch.setattr(
        stocks_router.StockDataService, "fetch_stock_info", classmethod(lambda cls, code: {"shortName": code})
    )
    monkeypatch.setattr(
        stocks_router.StockDataService,
        "fetch_real_price",
        classmethod(
            lambda cls, code: {
                "stock_code": code,
                "trade_date": date(2026, 4, 10),
                "open": 99.0,
                "high": 101.0,
                "low": 98.0,
                "close": 100.0,
                "volume": 12345,
            }
        ),
    )

    add = client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})
    assert add.status_code == 201
    watch_item = add.json()
    assert watch_item["date"] == "2026-04-10"
    assert isinstance(watch_item["price"], (int, float))

