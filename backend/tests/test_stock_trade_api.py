from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from db.database import SessionLocal
from models.stock import StockHoldingORM, StockPriceHistoryORM, StockTradeORM, WatchlistORM
from services.stock_trade_service import _replay_trades
from tests.conftest import auth_headers, register_and_login


def lookup_user_id(email: str) -> int:
    from models.user import UserORM

    with SessionLocal() as db:
        user = db.query(UserORM).filter(UserORM.email == email).one()
        return user.id


def seed_price(stock_code: str, close: float, *, user_id: int, currency: str = "USD", name: str | None = None) -> None:
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


def create_opening_holding(client, headers, stock_code: str = "AAPL", shares: float = 2, average_cost: float = 100):
    response = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": stock_code, "shares": shares, "average_cost": average_cost},
    )
    assert response.status_code == 201
    return response.json()


def create_trade(client, headers, stock_code: str, trade_type: str, trade_date: str, shares: float, price: float, **overrides):
    payload = {
        "stock_code": stock_code,
        "trade_type": trade_type,
        "trade_date": trade_date,
        "shares": shares,
        "price": price,
        "fee": overrides.pop("fee", 0),
        "tax": overrides.pop("tax", 0),
        **overrides,
    }
    response = client.post("/api/stocks/trades", headers=headers, json=payload)
    assert response.status_code == 201
    return response.json()


def test_holding_create_creates_opening_balance_trade(client):
    token = register_and_login(client, "trade-ledger-opening@example.com")
    headers = auth_headers(token)

    created = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "2330", "shares": 10, "average_cost": 900, "note": "Core position"},
    )
    assert created.status_code == 201
    holding = created.json()
    assert holding["stock_code"] == "2330.TW"
    assert holding["shares"] == 10

    trades = client.get("/api/stocks/trades", headers=headers)
    assert trades.status_code == 200
    payload = trades.json()
    assert len(payload) == 1
    assert payload[0]["trade_type"] == "OPENING_BALANCE"
    assert payload[0]["stock_code"] == "2330.TW"
    assert payload[0]["price"] == 900
    assert payload[0]["currency"] == "TWD"


def test_buy_sell_fifo_and_trade_summary(client):
    email = "trade-ledger-fifo@example.com"
    token = register_and_login(client, email)
    headers = auth_headers(token)
    seed_price("AAPL", 170, user_id=lookup_user_id(email), name="Apple")

    create_trade(client, headers, "AAPL", "BUY", "2026-07-01", 2, 100)

    buy_resp = client.post(
        "/api/stocks/trades",
        headers=headers,
        json={
            "stock_code": "AAPL",
            "trade_type": "BUY",
            "trade_date": "2026-07-02",
            "shares": 3,
            "price": 120,
            "fee": 6,
            "tax": 0,
            "note": "Add lot",
        },
    )
    assert buy_resp.status_code == 201

    sell_resp = client.post(
        "/api/stocks/trades",
        headers=headers,
        json={
            "stock_code": "AAPL",
            "trade_type": "SELL",
            "trade_date": "2026-07-03",
            "shares": 4,
            "price": 150,
            "fee": 5,
            "tax": 1,
            "note": "Take profit",
        },
    )
    assert sell_resp.status_code == 201

    holdings = client.get("/api/stocks/holdings", headers=headers)
    assert holdings.status_code == 200
    holding = holdings.json()[0]
    assert holding["stock_code"] == "AAPL"
    assert holding["shares"] == 1
    assert holding["average_cost"] == 122

    portfolio = client.get("/api/stocks/portfolio", headers=headers).json()
    assert portfolio["positions"][0]["cost_basis"] == 122
    assert portfolio["positions"][0]["unrealized_pnl"] == 48

    summary = client.get("/api/stocks/trades/summary", headers=headers)
    assert summary.status_code == 200
    item = summary.json()["items"][0]
    assert item["currency"] == "USD"
    assert item["opening_balance_count"] == 0
    assert item["opening_balance_shares"] == 0
    assert item["buy_count"] == 2
    assert item["sell_count"] == 1
    assert item["bought_shares"] == 5
    assert item["sold_shares"] == 4
    assert item["gross_proceeds"] == 600
    assert item["matched_cost_basis"] == 444
    assert item["fees"] == 11
    assert item["taxes"] == 1
    assert item["realized_pnl"] == 150


def test_oversell_is_rejected_and_rolls_back(client):
    token = register_and_login(client, "trade-ledger-oversell@example.com")
    headers = auth_headers(token)

    create_opening_holding(client, headers, "AAPL", shares=1, average_cost=100)
    response = client.post(
        "/api/stocks/trades",
        headers=headers,
        json={
            "stock_code": "AAPL",
            "trade_type": "SELL",
            "trade_date": "2026-07-02",
            "shares": 2,
            "price": 120,
            "fee": 0,
            "tax": 0,
        },
    )
    assert response.status_code == 409
    assert "negative inventory" in response.json()["detail"]

    trades = client.get("/api/stocks/trades", headers=headers).json()
    assert len(trades) == 1
    holdings = client.get("/api/stocks/holdings", headers=headers).json()
    assert holdings[0]["shares"] == 1


def test_holding_update_and_delete_block_when_buy_sell_history_exists(client):
    token = register_and_login(client, "trade-ledger-legacy-block@example.com")
    headers = auth_headers(token)

    holding = client.post(
        "/api/stocks/holdings",
        headers=headers,
        json={"stock_code": "AAPL", "shares": 2, "average_cost": 100},
    ).json()

    buy_response = client.post(
        "/api/stocks/trades",
        headers=headers,
        json={
            "stock_code": "AAPL",
            "trade_type": "BUY",
            "trade_date": "2026-07-02",
            "shares": 1,
            "price": 110,
            "fee": 0,
            "tax": 0,
        },
    )
    assert buy_response.status_code == 201

    update_response = client.put(
        f"/api/stocks/holdings/{holding['id']}",
        headers=headers,
        json={"shares": 4},
    )
    assert update_response.status_code == 409
    assert "managed through its trade ledger" in update_response.json()["detail"]

    delete_response = client.delete(f"/api/stocks/holdings/{holding['id']}", headers=headers)
    assert delete_response.status_code == 409
    assert "managed through its trade ledger" in delete_response.json()["detail"]


def test_trade_filters_and_user_isolation(client):
    token_a = register_and_login(client, "trade-ledger-scope-a@example.com")
    token_b = register_and_login(client, "trade-ledger-scope-b@example.com")

    for token, stock_code in ((token_a, "AAPL"), (token_b, "2330")):
        create_opening_holding(client, auth_headers(token), stock_code, shares=1, average_cost=100)

    list_a = client.get("/api/stocks/trades", headers=auth_headers(token_a), params={"stock_code": "AAPL"})
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1
    assert list_a.json()[0]["stock_code"] == "AAPL"

    list_b = client.get("/api/stocks/trades", headers=auth_headers(token_b))
    assert list_b.status_code == 200
    assert len(list_b.json()) == 1
    assert list_b.json()[0]["stock_code"] == "2330.TW"


def test_summary_filters_replay_complete_fifo_context(client):
    token = register_and_login(client, "trade-ledger-summary-filters@example.com")
    headers = auth_headers(token)
    create_trade(client, headers, "AAPL", "BUY", "2026-01-01", 10, 100)
    create_trade(client, headers, "AAPL", "SELL", "2026-02-01", 2, 130)
    create_trade(client, headers, "2330", "BUY", "2026-01-01", 10, 500)
    create_trade(client, headers, "2330", "SELL", "2026-02-01", 2, 560)

    sell_only = client.get("/api/stocks/trades/summary", headers=headers, params={"trade_type": "SELL"})
    assert sell_only.status_code == 200
    usd = next(item for item in sell_only.json()["items"] if item["currency"] == "USD")
    twd = next(item for item in sell_only.json()["items"] if item["currency"] == "TWD")
    assert usd["buy_count"] == 0
    assert usd["bought_shares"] == 0
    assert usd["sell_count"] == 1
    assert usd["sold_shares"] == 2
    assert usd["realized_pnl"] == 60
    assert twd["sold_shares"] == 2

    buy_only = client.get("/api/stocks/trades/summary", headers=headers, params={"trade_type": "BUY"})
    assert buy_only.status_code == 200
    assert buy_only.json()["items"][0]["sell_count"] == 0
    assert buy_only.json()["items"][0]["realized_pnl"] == 0

    date_from = client.get("/api/stocks/trades/summary", headers=headers, params={"date_from": "2026-02-01", "stock_code": "AAPL"})
    assert date_from.status_code == 200
    assert date_from.json()["items"][0]["realized_pnl"] == 60

    date_to = client.get("/api/stocks/trades/summary", headers=headers, params={"date_to": "2026-01-31"})
    assert date_to.status_code == 200
    assert all(item["sell_count"] == 0 for item in date_to.json()["items"])


def test_currency_reinference_and_conflicts(client):
    token = register_and_login(client, "trade-ledger-currency@example.com")
    headers = auth_headers(token)
    buy = create_trade(client, headers, "AAPL", "BUY", "2026-01-01", 5, 100)

    to_twd = client.put(f"/api/stocks/trades/{buy['id']}", headers=headers, json={"stock_code": "2330"})
    assert to_twd.status_code == 200
    assert to_twd.json()["stock_code"] == "2330.TW"
    assert to_twd.json()["currency"] == "TWD"

    shares_only = client.put(f"/api/stocks/trades/{buy['id']}", headers=headers, json={"shares": 6})
    assert shares_only.status_code == 200
    assert shares_only.json()["currency"] == "TWD"

    back_to_usd = client.put(f"/api/stocks/trades/{buy['id']}", headers=headers, json={"stock_code": "AAPL"})
    assert back_to_usd.status_code == 200
    assert back_to_usd.json()["currency"] == "USD"

    conflict = client.post(
        "/api/stocks/trades",
        headers=headers,
        json={"stock_code": "AAPL", "trade_type": "BUY", "trade_date": "2026-01-02", "shares": 1, "price": 100, "currency": "TWD"},
    )
    assert conflict.status_code == 409
    assert "different currency" in conflict.json()["detail"]


def test_currency_conflict_update_rolls_back_projection(client):
    token = register_and_login(client, "trade-ledger-currency-rollback@example.com")
    headers = auth_headers(token)
    first = create_trade(client, headers, "AAPL", "BUY", "2026-01-01", 5, 100)
    second = create_trade(client, headers, "AAPL", "BUY", "2026-01-02", 2, 50)

    response = client.put(f"/api/stocks/trades/{second['id']}", headers=headers, json={"currency": "TWD"})
    assert response.status_code == 409

    trades = client.get("/api/stocks/trades", headers=headers).json()
    assert {trade["stock_code"] for trade in trades} == {"AAPL"}
    assert {trade["currency"] for trade in trades} == {"USD"}
    holdings = client.get("/api/stocks/holdings", headers=headers).json()
    assert sorted((holding["stock_code"], holding["shares"]) for holding in holdings) == [("AAPL", 7)]


def test_defensive_replay_rejects_corrupted_mixed_currency_rows(client):
    token = register_and_login(client, "trade-ledger-corrupt@example.com")
    user_id = lookup_user_id("trade-ledger-corrupt@example.com")
    with SessionLocal() as db:
        db.add_all(
            [
                StockTradeORM(user_id=user_id, stock_code="AAPL", trade_type="BUY", trade_date=date(2026, 1, 1), shares=1, price=100, fee=0, tax=0, currency="USD"),
                StockTradeORM(user_id=user_id, stock_code="AAPL", trade_type="BUY", trade_date=date(2026, 1, 2), shares=1, price=100, fee=0, tax=0, currency="TWD"),
            ]
        )
        db.commit()
        rows = db.query(StockTradeORM).filter(StockTradeORM.user_id == user_id).order_by(StockTradeORM.id.asc()).all()
        try:
            _replay_trades(rows)
        except ValueError as exc:
            assert "mixed currencies" in str(exc)
        else:
            raise AssertionError("mixed-currency replay should fail")


def test_opening_balance_public_creation_and_duplicate_update_rejected(client):
    token = register_and_login(client, "trade-ledger-opening-rules@example.com")
    headers = auth_headers(token)
    create_opening_holding(client, headers, "AAPL", 2, 100)

    public_opening = client.post(
        "/api/stocks/trades",
        headers=headers,
        json={"stock_code": "AAPL", "trade_type": "OPENING_BALANCE", "trade_date": "2026-01-01", "shares": 1, "price": 100, "source": "client"},
    )
    assert public_opening.status_code == 409
    trades = client.get("/api/stocks/trades", headers=headers).json()
    assert "source" in trades[0]
    assert trades[0]["source"] == "legacy_holding"

    buy = create_trade(client, headers, "AAPL", "BUY", "2026-01-02", 1, 110)
    duplicate = client.put(f"/api/stocks/trades/{buy['id']}", headers=headers, json={"trade_type": "OPENING_BALANCE"})
    assert duplicate.status_code == 409
    holdings = client.get("/api/stocks/holdings", headers=headers).json()
    assert holdings[0]["shares"] == 3


def test_legacy_holding_update_delete_rebuild_projection(client):
    token = register_and_login(client, "trade-ledger-legacy-consistent@example.com")
    headers = auth_headers(token)
    holding = create_opening_holding(client, headers, "AAPL", 2, 100)

    updated = client.put(f"/api/stocks/holdings/{holding['id']}", headers=headers, json={"shares": 4})
    assert updated.status_code == 200
    assert updated.json()["shares"] == 4
    trades = client.get("/api/stocks/trades", headers=headers).json()
    assert len(trades) == 1
    assert trades[0]["shares"] == 4

    deleted = client.delete(f"/api/stocks/holdings/{holding['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/api/stocks/holdings", headers=headers).json() == []
    assert client.get("/api/stocks/trades", headers=headers).json() == []


def test_legacy_rename_rejects_any_target_history_and_rolls_back_source(client):
    token = register_and_login(client, "trade-ledger-rename-target@example.com")
    headers = auth_headers(token)
    holding = create_opening_holding(client, headers, "AAPL", 2, 100)
    create_trade(client, headers, "MSFT", "BUY", "2026-01-01", 1, 50)
    sell = create_trade(client, headers, "MSFT", "SELL", "2026-01-02", 1, 60)
    assert sell["stock_code"] == "MSFT"

    response = client.put(f"/api/stocks/holdings/{holding['id']}", headers=headers, json={"stock_code": "MSFT"})
    assert response.status_code == 409
    holdings = client.get("/api/stocks/holdings", headers=headers).json()
    assert len([row for row in holdings if row["stock_code"] == "AAPL"]) == 1

    valid = client.put(f"/api/stocks/holdings/{holding['id']}", headers=headers, json={"stock_code": "NVDA"})
    assert valid.status_code == 200
    assert valid.json()["stock_code"] == "NVDA"


def test_trade_query_validation(client):
    token = register_and_login(client, "trade-ledger-query-validation@example.com")
    headers = auth_headers(token)

    for path in ("/api/stocks/trades", "/api/stocks/trades/summary"):
        invalid_date = client.get(path, headers=headers, params={"date_from": "not-a-date"})
        assert invalid_date.status_code == 422
        invalid_type = client.get(path, headers=headers, params={"trade_type": "DIVIDEND"})
        assert invalid_type.status_code == 422
        inverted = client.get(path, headers=headers, params={"date_from": "2026-02-01", "date_to": "2026-01-01"})
        assert inverted.status_code == 422


def test_historical_mutations_keep_projection_consistent(client):
    token = register_and_login(client, "trade-ledger-historical@example.com")
    headers = auth_headers(token)
    buy1 = create_trade(client, headers, "AAPL", "BUY", "2026-01-01", 5, 100)
    buy2 = create_trade(client, headers, "AAPL", "BUY", "2026-01-01", 5, 120)
    sell = create_trade(client, headers, "AAPL", "SELL", "2026-01-02", 6, 150)

    holdings = client.get("/api/stocks/holdings", headers=headers).json()
    assert holdings[0]["shares"] == 4
    assert holdings[0]["average_cost"] == 120

    edit_sell = client.put(f"/api/stocks/trades/{sell['id']}", headers=headers, json={"shares": 5})
    assert edit_sell.status_code == 200
    holdings = client.get("/api/stocks/holdings", headers=headers).json()
    assert holdings[0]["shares"] == 5

    exact = client.put(f"/api/stocks/trades/{sell['id']}", headers=headers, json={"shares": 10})
    assert exact.status_code == 200
    assert client.get("/api/stocks/holdings", headers=headers).json() == []

    restore_inventory = client.put(f"/api/stocks/trades/{sell['id']}", headers=headers, json={"shares": 6})
    assert restore_inventory.status_code == 200

    bad_edit = client.put(f"/api/stocks/trades/{buy1['id']}", headers=headers, json={"shares": 0.5})
    assert bad_edit.status_code == 409
    holdings = client.get("/api/stocks/holdings", headers=headers).json()
    assert holdings[0]["shares"] == 4

    bad_delete = client.delete(f"/api/stocks/trades/{buy1['id']}", headers=headers)
    assert bad_delete.status_code == 409
    ok_delete_sell = client.delete(f"/api/stocks/trades/{sell['id']}", headers=headers)
    assert ok_delete_sell.status_code == 204
    holdings = client.get("/api/stocks/holdings", headers=headers).json()
    assert holdings[0]["shares"] == 10


def test_one_user_cannot_update_or_delete_another_users_trade(client):
    token_a = register_and_login(client, "trade-ledger-owner-a@example.com")
    token_b = register_and_login(client, "trade-ledger-owner-b@example.com")
    trade = create_trade(client, auth_headers(token_a), "AAPL", "BUY", "2026-01-01", 1, 100)

    update = client.put(f"/api/stocks/trades/{trade['id']}", headers=auth_headers(token_b), json={"shares": 2})
    assert update.status_code == 404
    delete = client.delete(f"/api/stocks/trades/{trade['id']}", headers=auth_headers(token_b))
    assert delete.status_code == 404
