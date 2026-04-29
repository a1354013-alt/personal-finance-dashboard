from __future__ import annotations

from datetime import date

import pytest

from routers import stocks as stocks_router
from tests.conftest import auth_headers, drain_jobs, register_and_login


def mock_history(stock_code: str, close: float = 100.0, trade_date: date = date(2026, 4, 10)) -> list[dict]:
    return [
        {
            "stock_code": stock_code,
            "trade_date": trade_date,
            "open": close - 1,
            "high": close + 1,
            "low": close - 2,
            "close": close,
            "volume": 12345,
        }
    ]


def test_auth_register_login_me(client):
    token = register_and_login(client, "smoke@example.com")
    me_response = client.get("/api/auth/me", headers=auth_headers(token))
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "smoke@example.com"


def test_refresh_token_flow(client):
    client.post("/api/auth/register", json={"email": "refresh@example.com", "password": "password123"})
    login = client.post("/api/auth/login", json={"email": "refresh@example.com", "password": "password123"})
    assert login.status_code == 200
    refresh = client.post("/api/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]
    assert refresh.json()["refresh_token"] != login.json()["refresh_token"]


def test_expenses_budgets_and_dashboard_flow(client):
    token = register_and_login(client, "budget@example.com")

    client.post("/api/budgets", headers=auth_headers(token), json={"category": "Food", "monthly_limit": 1000})
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 3000, "category": "Salary", "type": "income", "date": "2026-04-01", "note": "Salary"},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 700, "category": "Food", "type": "expense", "date": "2026-04-05", "note": "Groceries"},
    )

    dashboard = client.get("/api/dashboard/summary", headers=auth_headers(token))
    assert dashboard.status_code == 200
    assert dashboard.json()["total_income"] == 3000
    assert dashboard.json()["total_expense"] == 700

    charts = client.get("/api/dashboard/charts", headers=auth_headers(token))
    assert charts.status_code == 200
    assert charts.json()["category_distribution"][0]["category"] == "Food"


def test_stocks_watchlist_syncs_in_background(client, monkeypatch: pytest.MonkeyPatch):
    token = register_and_login(client, "stocks@example.com")

    monkeypatch.setattr(stocks_router.StockDataService, "fetch_stock_info", classmethod(lambda cls, code: {"shortName": code}))
    monkeypatch.setattr(stocks_router.StockDataService, "fetch_price_history", classmethod(lambda cls, code: mock_history(code, close=321.0)))

    add_response = client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "NVDA"})
    assert add_response.status_code == 201
    assert add_response.json()["price_sync_status"] == "pending"

    drain_jobs()

    watchlist = client.get("/api/stocks/watchlist", headers=auth_headers(token))
    assert watchlist.status_code == 200
    assert watchlist.json()[0]["price_sync_status"] == "success"
    assert watchlist.json()[0]["price"] == 321.0

    dashboard = client.get("/api/stocks/dashboard", headers=auth_headers(token))
    assert dashboard.status_code == 200
    assert dashboard.json()["watchlist"][0]["stock_code"] == "NVDA"
    assert dashboard.json()["price_history"][0]["close"] == 321.0
