from __future__ import annotations

from datetime import date, datetime, timezone

from db.database import SessionLocal
from models.stock import StockPriceHistoryORM, WatchlistORM
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

    open_resp = client.post(
        "/api/stocks/trades",
        headers=headers,
        json={
            "stock_code": "AAPL",
            "trade_type": "OPENING_BALANCE",
            "trade_date": "2026-07-01",
            "shares": 2,
            "price": 100,
            "fee": 0,
            "tax": 0,
            "note": "Legacy start",
        },
    )
    assert open_resp.status_code == 201

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
    assert item["buy_count"] == 1
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

    client.post(
        "/api/stocks/trades",
        headers=headers,
        json={
            "stock_code": "AAPL",
            "trade_type": "OPENING_BALANCE",
            "trade_date": "2026-07-01",
            "shares": 1,
            "price": 100,
            "fee": 0,
            "tax": 0,
        },
    )
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
        response = client.post(
            "/api/stocks/trades",
            headers=auth_headers(token),
            json={
                "stock_code": stock_code,
                "trade_type": "OPENING_BALANCE",
                "trade_date": "2026-07-01",
                "shares": 1,
                "price": 100,
                "fee": 0,
                "tax": 0,
            },
        )
        assert response.status_code == 201

    list_a = client.get("/api/stocks/trades", headers=auth_headers(token_a), params={"stock_code": "AAPL"})
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1
    assert list_a.json()[0]["stock_code"] == "AAPL"

    list_b = client.get("/api/stocks/trades", headers=auth_headers(token_b))
    assert list_b.status_code == 200
    assert len(list_b.json()) == 1
    assert list_b.json()[0]["stock_code"] == "2330.TW"
