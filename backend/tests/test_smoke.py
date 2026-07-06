from __future__ import annotations

from datetime import date, datetime

import pytest

from providers.stock_price.base import StockQuote
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


def test_root_endpoint_uses_utc_z_timestamp(client):
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["generated_at"].endswith("Z")
    parsed = datetime.fromisoformat(payload["generated_at"].replace("Z", "+00:00"))
    assert parsed.tzinfo is not None


def test_expenses_budgets_and_dashboard_flow(client):
    token = register_and_login(client, "budget@example.com")

    current_month = date.today().strftime("%Y-%m")
    client.post("/api/budgets", headers=auth_headers(token), json={"month": current_month, "category": "Food", "amount": 1000})
    today = date.today().strftime("%Y-%m-%d")
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 3000, "category": "Salary", "type": "income", "date": today, "note": "Salary"},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 700, "category": "Food", "type": "expense", "date": today, "note": "Groceries"},
    )

    dashboard = client.get("/api/dashboard/summary", headers=auth_headers(token))
    assert dashboard.status_code == 200
    assert dashboard.json()["monthlyIncome"] == 3000
    assert dashboard.json()["monthlyExpense"] == 700
    assert dashboard.json()["budgetItems"][0]["amount"] == 1000

    charts = client.get("/api/dashboard/charts", headers=auth_headers(token))
    assert charts.status_code == 200
    assert charts.json()["category_distribution"][0]["category"] == "Food"
    assert charts.json()["budget_usage"][0]["amount"] == 1000


def test_stocks_watchlist_syncs_in_background(client, monkeypatch: pytest.MonkeyPatch):
    token = register_and_login(client, "stocks@example.com")

    class FakeProvider:
        name = "fake"

        def normalize_symbol(self, stock_code: str) -> str:
            return stock_code.strip().upper()

        def infer_market(self, _stock_code: str) -> tuple[str, str | None, str]:
            return "US", None, "USD"

        def fetch_quote(self, stock_code: str):
            row = mock_history(stock_code, close=321.0)[0]
            return StockQuote(
                stock_code=stock_code,
                name=stock_code,
                market="US",
                exchange=None,
                currency="USD",
                trade_date=row["trade_date"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                previous_close=320.0,
                volume=row["volume"],
                provider=self.name,
            )

    monkeypatch.setattr("services.watchlist_service.get_stock_price_provider", lambda: FakeProvider())
    monkeypatch.setattr("services.stock_data_service.get_stock_price_provider", lambda: FakeProvider())

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
