from __future__ import annotations

from datetime import date

import pytest

from models.stock import WatchlistORM
from providers.stock_price.base import StockQuote
from tests.conftest import auth_headers, register_and_login


class FakeTaiwanProvider:
    name = "fake-taiwan"

    def __init__(self, quote: StockQuote | None):
        self.quote = quote

    def normalize_symbol(self, stock_code: str) -> str:
        code = stock_code.strip().upper()
        if code.isdigit() and len(code) == 4:
            return f"{code}.TW"
        return code

    def infer_market(self, stock_code: str) -> tuple[str, str | None, str]:
        normalized = self.normalize_symbol(stock_code)
        if normalized.endswith(".TW"):
            return "Taiwan", "TWSE", "TWD"
        return "US", None, "USD"

    def fetch_quote(self, stock_code: str) -> StockQuote | None:
        return self.quote


@pytest.fixture()
def fake_provider(monkeypatch):
    provider = FakeTaiwanProvider(
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
            provider="fake-taiwan",
        )
    )
    monkeypatch.setattr("services.watchlist_service.get_stock_price_provider", lambda: provider)
    monkeypatch.setattr("services.stock_data_service.get_stock_price_provider", lambda: provider)
    return provider


def test_add_taiwan_stock_normalizes_symbol_and_rejects_duplicate(client, fake_provider):
    token = register_and_login(client, "tw-duplicate@example.com")
    headers = auth_headers(token)

    first = client.post("/api/stocks/watchlist", headers=headers, json={"stock_code": "2330"})
    assert first.status_code == 201
    assert first.json()["stock_code"] == "2330.TW"
    assert first.json()["market"] == "Taiwan"
    assert first.json()["currency"] == "TWD"

    duplicate = client.post("/api/stocks/watchlist", headers=headers, json={"stock_code": "2330"})
    assert duplicate.status_code == 400


def test_watchlist_item_sync_success_with_fake_provider(client, fake_provider):
    token = register_and_login(client, "tw-sync@example.com")
    headers = auth_headers(token)
    item = client.post("/api/stocks/watchlist", headers=headers, json={"stock_code": "2330"}).json()

    synced = client.post(f"/api/stocks/watchlist/{item['id']}/sync", headers=headers)
    assert synced.status_code == 200
    payload = synced.json()
    assert payload["sync_status"] == "ready"
    assert payload["last_price"] == 1000
    assert payload["previous_close"] == 950
    assert payload["price_change"] == 50
    assert round(payload["change_percent"], 2) == 5.26
    assert payload["volume"] == 12345678
    assert payload["provider"] == "fake-taiwan"


def test_watchlist_item_sync_failure_is_graceful(client, fake_provider):
    fake_provider.quote = None
    token = register_and_login(client, "tw-sync-fail@example.com")
    headers = auth_headers(token)
    item = client.post("/api/stocks/watchlist", headers=headers, json={"stock_code": "0050"}).json()

    synced = client.post(f"/api/stocks/watchlist/{item['id']}/sync", headers=headers)
    assert synced.status_code == 200
    payload = synced.json()
    assert payload["sync_status"] == "error"
    assert payload["sync_required"] is True
    assert "Unable to fetch" in payload["sync_error"]


def test_watchlist_item_access_is_user_scoped(client, fake_provider):
    token_a = register_and_login(client, "tw-user-a@example.com")
    token_b = register_and_login(client, "tw-user-b@example.com")
    item = client.post("/api/stocks/watchlist", headers=auth_headers(token_a), json={"stock_code": "2330"}).json()

    response = client.post(f"/api/stocks/watchlist/{item['id']}/sync", headers=auth_headers(token_b))
    assert response.status_code == 404


def test_stock_dashboard_rejects_selected_code_outside_user_watchlist(client, fake_provider):
    token_a = register_and_login(client, "tw-dashboard-user-a@example.com")
    token_b = register_and_login(client, "tw-dashboard-user-b@example.com")
    headers_a = auth_headers(token_a)
    headers_b = auth_headers(token_b)

    client.post("/api/stocks/watchlist", headers=headers_a, json={"stock_code": "2330"})
    client.post("/api/stocks/watchlist", headers=headers_b, json={"stock_code": "0050"})

    response = client.get("/api/stocks/dashboard", headers=headers_b, params={"selected_code": "2330"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Selected stock is not in your watchlist."


def test_ai_analysis_requires_synced_price_data(client, fake_provider):
    token = register_and_login(client, "tw-ai-required@example.com")
    headers = auth_headers(token)
    item = client.post("/api/stocks/watchlist", headers=headers, json={"stock_code": "2330"}).json()

    response = client.post(f"/api/stocks/watchlist/{item['id']}/ai-analysis", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "sync_required"


def test_ai_analysis_returns_interpretation_and_disclaimer(client, fake_provider, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "fallback")
    from providers.llm.factory import reset_llm_provider_cache

    reset_llm_provider_cache()
    token = register_and_login(client, "tw-ai-ready@example.com")
    headers = auth_headers(token)
    item = client.post("/api/stocks/watchlist", headers=headers, json={"stock_code": "2330"}).json()
    client.post(f"/api/stocks/watchlist/{item['id']}/sync", headers=headers)

    response = client.post(f"/api/stocks/watchlist/{item['id']}/ai-analysis", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert "This is informational only and not financial advice." in payload["summary"]
    assert payload["risk_notes"]
    assert payload["watch_points"]
    forbidden = ["buy", "sell", "must buy", "guaranteed", "target price"]
    assert not any(word in payload["summary"].lower() for word in forbidden)
