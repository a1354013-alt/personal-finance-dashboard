from __future__ import annotations

from datetime import date

import pytest

from providers.stock_price.base import StockQuote
from tests.conftest import drain_jobs


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
    assert "user_id" not in payload
    assert isinstance(payload["amount"], (int, float))
    assert payload["date"] == "2026-04-10"

    budget = client.post(
        "/api/budgets",
        headers=auth_headers(token),
        json={"month": "2026-04", "category": "Food", "amount": 1000},
    )
    assert budget.status_code in {200, 201}
    budget_payload = budget.json()
    assert "user_id" not in budget_payload
    assert "created_at" not in budget_payload

    class FakeProvider:
        name = "fake"

        def normalize_symbol(self, stock_code: str) -> str:
            return stock_code.strip().upper()

        def infer_market(self, _stock_code: str) -> tuple[str, str | None, str]:
            return "US", None, "USD"

        def fetch_quote(self, stock_code: str):
            return StockQuote(
                stock_code=stock_code,
                name=stock_code,
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

    monkeypatch.setattr("services.watchlist_service.get_stock_price_provider", lambda: FakeProvider())
    monkeypatch.setattr("services.stock_data_service.get_stock_price_provider", lambda: FakeProvider())

    add = client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})
    assert add.status_code == 201

    sync = client.post("/api/stocks/AAPL/sync", headers=auth_headers(token))
    assert sync.status_code == 200
    assert sync.json()["price_sync_status"] == "pending"
    drain_jobs()

    watch_item = client.get("/api/stocks/watchlist", headers=auth_headers(token)).json()[0]
    assert watch_item["date"] == "2026-04-10"
    assert isinstance(watch_item["price"], (int, float))
    assert watch_item["currency"] == "USD"
    assert "user_id" not in watch_item


def test_watchlist_contract_infers_currency_per_item(client):
    token = register_and_login(client, "stock-currency@example.com")

    add_tw = client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "2330.TW"})
    add_us = client.post("/api/stocks/watchlist", headers=auth_headers(token), json={"stock_code": "AAPL"})
    assert add_tw.status_code == 201
    assert add_us.status_code == 201

    dashboard = client.get("/api/stocks/dashboard", headers=auth_headers(token))
    assert dashboard.status_code == 200
    currency_by_code = {item["stock_code"]: item["currency"] for item in dashboard.json()["watchlist"]}
    assert currency_by_code["2330.TW"] == "TWD"
    assert currency_by_code["AAPL"] == "USD"


def test_portfolio_contract_serializes_numbers_without_user_scope_leak(client):
    token = register_and_login(client, "portfolio-contract@example.com")
    headers = auth_headers(token)

    holding = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "AAPL", "shares": 2.5, "average_cost": 120.25, "note": "taxable"},
    )
    assert holding.status_code == 201
    holding_payload = holding.json()
    assert "user_id" not in holding_payload
    assert isinstance(holding_payload["shares"], (int, float))
    assert isinstance(holding_payload["average_cost"], (int, float))

    portfolio = client.get("/api/stocks/portfolio", headers=headers)
    assert portfolio.status_code == 200
    payload = portfolio.json()
    assert isinstance(payload["total_cost"], (int, float))
    assert payload["positions"][0]["latest_price"] is None

