from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from db.database import SessionLocal
from models.stock import StockPriceHistoryORM, WatchlistORM
from models.user import UserORM
from tests.conftest import auth_headers, register_and_login


def lookup_user_id(email: str) -> int:
    with SessionLocal() as db:
        user = db.query(UserORM).filter(UserORM.email == email).one()
        return user.id


def seed_price(
    stock_code: str,
    close: float,
    *,
    user_id: int | None = None,
    currency: str = "USD",
    name: str | None = None,
) -> None:
    with SessionLocal() as db:
        db.add(
            StockPriceHistoryORM(
                stock_code=stock_code,
                trade_date=date(2026, 7, 12),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000,
                source="test",
            )
        )
        if user_id is not None:
            db.add(
                WatchlistORM(
                    user_id=user_id,
                    stock_code=stock_code,
                    name=name or stock_code,
                    market="Taiwan" if stock_code.endswith(".TW") else "US",
                    exchange="TWSE" if stock_code.endswith(".TW") else None,
                    currency=currency,
                    last_price=close,
                    previous_close=close,
                    price_change=0,
                    change_percent=0,
                    volume=1000,
                    provider="test",
                    price_updated_at=datetime.now(timezone.utc),
                    sync_status="ready",
                    sync_required=0,
                    price_sync_status="success",
                    last_sync_attempt_at=datetime.now(timezone.utc),
                )
            )
        db.commit()


def test_create_list_update_delete_holding(client):
    token = register_and_login(client, "portfolio-crud@example.com")
    headers = auth_headers(token)

    created = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "2330", "shares": 10, "average_cost": 950, "note": "Core position"},
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["stock_code"] == "2330.TW"
    assert payload["shares"] == 10
    assert payload["average_cost"] == 950
    assert payload["currency"] == "TWD"
    assert payload["note"] == "Core position"

    listed = client.get("/api/stocks/holdings", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.put(
        f"/api/stocks/holdings/{payload['id']}",
        headers=headers,
        json={"shares": 12, "average_cost": 930},
    )
    assert updated.status_code == 200
    assert updated.json()["shares"] == 12
    assert updated.json()["average_cost"] == 930

    deleted = client.delete(f"/api/stocks/holdings/{payload['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/api/stocks/holdings", headers=headers).json() == []


def test_reject_duplicate_holding_for_same_user_and_stock(client):
    token = register_and_login(client, "portfolio-duplicate@example.com")
    headers = auth_headers(token)

    first = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "AAPL", "shares": 2, "average_cost": 150},
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "AAPL", "shares": 1, "average_cost": 160},
    )
    assert duplicate.status_code == 400
    assert "already exists" in duplicate.json()["detail"]


def test_list_current_user_holdings_only(client):
    token_a = register_and_login(client, "portfolio-user-a@example.com")
    token_b = register_and_login(client, "portfolio-user-b@example.com")
    client.post("/api/stocks/holdings", headers=auth_headers(token_a), json={"stock_code": "AAPL", "shares": 2, "average_cost": 150})
    client.post("/api/stocks/holdings", headers=auth_headers(token_b), json={"stock_code": "2330", "shares": 4, "average_cost": 900})

    response = client.get("/api/stocks/holdings", headers=auth_headers(token_a))
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["stock_code"] == "AAPL"


def test_reject_invalid_shares_and_average_cost(client):
    token = register_and_login(client, "portfolio-invalid@example.com")
    headers = auth_headers(token)

    invalid_shares = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "AAPL", "shares": 0, "average_cost": 150},
    )
    assert invalid_shares.status_code == 422

    invalid_average_cost = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "AAPL", "shares": 1, "average_cost": -1},
    )
    assert invalid_average_cost.status_code == 422


def test_cross_user_holding_access_blocked(client):
    token_a = register_and_login(client, "portfolio-guard-a@example.com")
    token_b = register_and_login(client, "portfolio-guard-b@example.com")

    created = client.post(
        "/api/stocks/holdings",
        headers=auth_headers(token_a),
        json={"stock_code": "AAPL", "shares": 3, "average_cost": 150},
    ).json()

    assert client.put(
        f"/api/stocks/holdings/{created['id']}",
        headers=auth_headers(token_b),
        json={"shares": 5},
    ).status_code == 404
    assert client.delete(f"/api/stocks/holdings/{created['id']}", headers=auth_headers(token_b)).status_code == 404


def test_update_holding_reinfers_currency_when_stock_code_changes(client):
    token = register_and_login(client, "portfolio-edit-currency@example.com")
    headers = auth_headers(token)

    aapl = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "AAPL", "shares": 3, "average_cost": 150},
    ).json()
    to_taiwan = client.put(
        f"/api/stocks/holdings/{aapl['id']}",
        headers=headers,
        json={"stock_code": "2330"},
    )
    assert to_taiwan.status_code == 200
    assert to_taiwan.json()["stock_code"] == "2330.TW"
    assert to_taiwan.json()["currency"] == "TWD"

    to_us = client.put(
        f"/api/stocks/holdings/{aapl['id']}",
        headers=headers,
        json={"stock_code": "AAPL"},
    )
    assert to_us.status_code == 200
    assert to_us.json()["stock_code"] == "AAPL"
    assert to_us.json()["currency"] == "USD"


def test_update_holding_preserves_currency_without_stock_code_change(client):
    token = register_and_login(client, "portfolio-edit-preserve-currency@example.com")
    headers = auth_headers(token)

    created = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "2330", "shares": 3, "average_cost": 900},
    ).json()
    updated = client.put(
        f"/api/stocks/holdings/{created['id']}",
        headers=headers,
        json={"shares": 4, "average_cost": 880},
    )
    assert updated.status_code == 200
    assert updated.json()["currency"] == "TWD"


def test_update_holding_respects_explicit_currency(client):
    token = register_and_login(client, "portfolio-edit-explicit-currency@example.com")
    headers = auth_headers(token)

    created = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "AAPL", "shares": 3, "average_cost": 150},
    ).json()
    updated = client.put(
        f"/api/stocks/holdings/{created['id']}",
        headers=headers,
        json={"stock_code": "2330", "currency": "USD"},
    )
    assert updated.status_code == 200
    assert updated.json()["stock_code"] == "2330.TW"
    assert updated.json()["currency"] == "USD"


def test_update_holding_duplicate_error_names_target_and_preserves_original(client):
    token = register_and_login(client, "portfolio-edit-duplicate@example.com")
    headers = auth_headers(token)

    client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "AAPL", "shares": 3, "average_cost": 150},
    )
    msft = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "MSFT", "shares": 2, "average_cost": 300},
    ).json()

    duplicate_update = client.put(
        f"/api/stocks/holdings/{msft['id']}",
        headers=headers,
        json={"stock_code": "AAPL"},
    )
    assert duplicate_update.status_code == 400
    assert "AAPL" in duplicate_update.json()["detail"]
    assert "MSFT" not in duplicate_update.json()["detail"]

    holdings = client.get("/api/stocks/holdings", headers=headers).json()
    codes = [item["stock_code"] for item in holdings]
    assert codes.count("AAPL") == 1
    assert codes.count("MSFT") == 1
    assert next(item for item in holdings if item["id"] == msft["id"])["stock_code"] == "MSFT"


def test_portfolio_summary_with_one_holding(client):
    email = "portfolio-summary-one@example.com"
    token = register_and_login(client, email)
    headers = auth_headers(token)

    seed_price("AAPL", 180, user_id=lookup_user_id(email), name="Apple")
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "AAPL", "shares": 2, "average_cost": 150})

    response = client.get("/api/stocks/portfolio", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_cost"] == 300
    assert payload["total_market_value"] == 360
    assert payload["total_unrealized_pnl"] == 60
    assert payload["total_unrealized_pnl_percent"] == 20
    assert payload["holdings_count"] == 1
    assert payload["currency"] == "USD"
    assert payload["currency_totals"] == [
        {
            "currency": "USD",
            "total_cost": 300,
            "total_market_value": 360,
            "total_unrealized_pnl": 60,
            "total_unrealized_pnl_percent": 20,
            "priced_cost": 300,
            "unpriced_cost": 0,
            "holdings_count": 1,
            "priced_holdings_count": 1,
            "missing_price_count": 0,
            "is_partial": False,
        }
    ]
    assert payload["positions"][0]["stock_name"] == "Apple"
    assert payload["positions"][0]["allocation_percent"] == 100


def test_portfolio_summary_with_multiple_holdings_same_currency_allocations(client):
    email = "portfolio-summary-many-us@example.com"
    token = register_and_login(client, email)
    headers = auth_headers(token)

    user_id = lookup_user_id(email)
    seed_price("AAPL", 200, user_id=user_id, name="Apple")
    seed_price("MSFT", 400, user_id=user_id, name="Microsoft")
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "AAPL", "shares": 1, "average_cost": 150})
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "MSFT", "shares": 2, "average_cost": 300})

    response = client.get("/api/stocks/portfolio", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["currency"] == "USD"
    assert payload["total_cost"] == 750
    assert payload["total_market_value"] == 1000
    assert payload["total_unrealized_pnl"] == 250
    assert round(payload["total_unrealized_pnl_percent"], 2) == 33.33
    positions = {item["stock_code"]: item for item in payload["positions"]}
    assert round(positions["AAPL"]["allocation_percent"], 2) == 20.00
    assert round(positions["MSFT"]["allocation_percent"], 2) == 80.00


def test_portfolio_summary_groups_mixed_currency_totals_without_combining_them(client):
    email = "portfolio-summary-many@example.com"
    token = register_and_login(client, email)
    headers = auth_headers(token)

    user_id = lookup_user_id(email)
    seed_price("AAPL", 200, user_id=user_id, name="Apple")
    seed_price("2330.TW", 1000, user_id=user_id, currency="TWD", name="TSMC")
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "AAPL", "shares": 1, "average_cost": 150})
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "2330", "shares": 2, "average_cost": 900})

    response = client.get("/api/stocks/portfolio", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["currency"] is None
    assert payload["total_cost"] is None
    assert payload["total_market_value"] is None
    assert payload["total_unrealized_pnl"] is None
    assert payload["total_unrealized_pnl_percent"] is None
    assert any("Portfolio contains multiple currencies: TWD, USD." in warning for warning in payload["warnings"])
    totals = {item["currency"]: item for item in payload["currency_totals"]}
    assert totals["USD"]["total_cost"] == 150
    assert totals["USD"]["total_market_value"] == 200
    assert totals["USD"]["total_unrealized_pnl"] == 50
    assert round(totals["USD"]["total_unrealized_pnl_percent"], 2) == 33.33
    assert totals["TWD"]["total_cost"] == 1800
    assert totals["TWD"]["total_market_value"] == 2000
    assert totals["TWD"]["total_unrealized_pnl"] == 200
    assert round(totals["TWD"]["total_unrealized_pnl_percent"], 2) == 11.11
    assert totals["USD"]["priced_cost"] == 150
    assert totals["TWD"]["priced_cost"] == 1800
    assert totals["USD"]["missing_price_count"] == 0
    assert totals["TWD"]["missing_price_count"] == 0
    positions = {item["stock_code"]: item for item in payload["positions"]}
    assert positions["AAPL"]["allocation_percent"] == 100
    assert positions["2330.TW"]["allocation_percent"] == 100


def test_portfolio_summary_handles_missing_price_gracefully(client):
    token = register_and_login(client, "portfolio-missing-price@example.com")
    headers = auth_headers(token)

    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "MSFT", "shares": 2, "average_cost": 300})
    response = client.get("/api/stocks/portfolio", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_cost"] == 600
    assert payload["total_market_value"] is None
    assert payload["total_unrealized_pnl"] is None
    assert payload["currency_totals"] == [
        {
            "currency": "USD",
            "total_cost": 600,
            "total_market_value": None,
            "total_unrealized_pnl": None,
            "total_unrealized_pnl_percent": None,
            "priced_cost": 0,
            "unpriced_cost": 600,
            "holdings_count": 1,
            "priced_holdings_count": 0,
            "missing_price_count": 1,
            "is_partial": True,
        }
    ]
    assert payload["warnings"]
    assert payload["positions"][0]["latest_price"] is None
    assert payload["positions"][0]["market_value"] is None
    assert payload["positions"][0]["warning"]


def test_portfolio_summary_marks_single_currency_partial_price_totals(client):
    email = "portfolio-partial-same-currency@example.com"
    token = register_and_login(client, email)
    headers = auth_headers(token)

    user_id = lookup_user_id(email)
    seed_price("AAPL", 180, user_id=user_id, name="Apple")
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "AAPL", "shares": 2, "average_cost": 150})
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "MSFT", "shares": 1, "average_cost": 300})

    response = client.get("/api/stocks/portfolio", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    total = payload["currency_totals"][0]
    assert total["currency"] == "USD"
    assert total["holdings_count"] == 2
    assert total["priced_holdings_count"] == 1
    assert total["missing_price_count"] == 1
    assert total["is_partial"] is True
    assert total["total_cost"] == 600
    assert total["priced_cost"] == 300
    assert total["unpriced_cost"] == 300
    assert total["total_market_value"] == 360
    assert total["total_unrealized_pnl"] == 60
    positions = {item["stock_code"]: item for item in payload["positions"]}
    assert positions["AAPL"]["allocation_percent"] == 100
    assert positions["MSFT"]["latest_price"] is None
    assert positions["MSFT"]["market_value"] is None
    assert positions["MSFT"]["allocation_percent"] is None


def test_portfolio_summary_uses_same_currency_denominator_for_partial_mixed_portfolios(client):
    email = "portfolio-partial-mixed-currency@example.com"
    token = register_and_login(client, email)
    headers = auth_headers(token)

    user_id = lookup_user_id(email)
    seed_price("2330.TW", 1000, user_id=user_id, currency="TWD", name="TSMC")
    seed_price("AAPL", 200, user_id=user_id, name="Apple")
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "2330", "shares": 2, "average_cost": 900})
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "0050", "shares": 1, "average_cost": 150})
    client.post("/api/stocks/holdings", headers=headers, json={"stock_code": "AAPL", "shares": 1, "average_cost": 150})

    response = client.get("/api/stocks/portfolio", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    totals = {item["currency"]: item for item in payload["currency_totals"]}
    assert totals["TWD"]["is_partial"] is True
    assert totals["TWD"]["total_market_value"] == 2000
    assert totals["TWD"]["priced_holdings_count"] == 1
    assert totals["TWD"]["missing_price_count"] == 1

    positions = {item["stock_code"]: item for item in payload["positions"]}
    assert positions["2330.TW"]["allocation_percent"] == 100
    assert positions["0050.TW"]["allocation_percent"] is None
    assert positions["AAPL"]["allocation_percent"] == 100


def test_portfolio_summary_excludes_cross_user_holdings(client):
    email_a = "portfolio-scope-a@example.com"
    token_a = register_and_login(client, email_a)
    token_b = register_and_login(client, "portfolio-scope-b@example.com")

    seed_price("AAPL", 180, user_id=lookup_user_id(email_a), name="Apple")
    client.post("/api/stocks/holdings", headers=auth_headers(token_a), json={"stock_code": "AAPL", "shares": 1, "average_cost": 100})
    client.post("/api/stocks/holdings", headers=auth_headers(token_b), json={"stock_code": "AAPL", "shares": 10, "average_cost": 100})

    response = client.get("/api/stocks/portfolio", headers=auth_headers(token_a))
    assert response.status_code == 200
    assert response.json()["holdings_count"] == 1
    assert response.json()["total_cost"] == 100


def test_seeded_demo_portfolio_has_twd_and_usd_summaries(client):
    from seed_data import DEMO_EMAIL, DEMO_PASSWORD, seed

    seed(reset=True, relative_dates=False)
    login_response = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get("/api/stocks/portfolio", headers=auth_headers(token))
    assert response.status_code == 200
    payload = response.json()
    totals = {item["currency"]: item for item in payload["currency_totals"]}
    assert payload["currency"] is None
    assert payload["total_market_value"] is None
    assert any("Portfolio contains multiple currencies: TWD, USD." in warning for warning in payload["warnings"])
    assert set(totals) == {"TWD", "USD"}
    assert totals["TWD"]["holdings_count"] == 2
    assert totals["USD"]["holdings_count"] == 1
