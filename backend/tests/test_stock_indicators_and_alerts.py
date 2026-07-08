from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from db.database import SessionLocal
from models.stock import StockPriceHistoryORM, WatchlistORM
from services.stock_indicator_service import calculate_rsi14
from tests.conftest import auth_headers, register_and_login


def _add_history(stock_code: str, closes: list[float], *, start: date = date(2026, 6, 1)) -> None:
    with SessionLocal() as db:
        for index, close in enumerate(closes):
            db.add(
                StockPriceHistoryORM(
                    stock_code=stock_code,
                    trade_date=start + timedelta(days=index * 2),
                    open=Decimal(str(close - 1)),
                    high=Decimal(str(close + 1)),
                    low=Decimal(str(close - 2)),
                    close=Decimal(str(close)),
                    volume=1000 + index,
                    source="test",
                )
            )
        db.commit()


def _set_watchlist_price(item_id: int, price: float) -> None:
    with SessionLocal() as db:
        item = db.query(WatchlistORM).filter(WatchlistORM.id == item_id).one()
        item.last_price = Decimal(str(price))
        item.sync_status = "ready"
        item.sync_required = 0
        item.price_sync_status = "success"
        db.commit()


def _create_watchlist_item(client, headers, stock_code: str = "2330") -> dict:
    response = client.post("/api/stocks/watchlist", headers=headers, json={"stock_code": stock_code})
    assert response.status_code == 201
    return response.json()


def test_indicator_service_returns_ready_values_for_enough_taiwan_history(client):
    token = register_and_login(client, "indicator-ready@example.com")
    headers = auth_headers(token)
    item = _create_watchlist_item(client, headers, "2330")
    _add_history("2330.TW", [100 + index for index in range(20)])

    response = client.get(f"/api/stocks/watchlist/{item['id']}/indicators", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["watchlist_item_id"] == item["id"]
    assert payload["symbol"] == "2330.TW"
    assert payload["as_of_date"] == "2026-07-09"
    assert payload["latest_close"] == 119
    assert payload["ma5"] == 117
    assert payload["ma20"] == 109.5
    assert payload["rsi14"] == 100
    assert payload["status"] == "ready"
    assert "not financial advice" in payload["disclaimer"]


def test_indicator_api_returns_insufficient_history_and_empty_history(client):
    token = register_and_login(client, "indicator-insufficient@example.com")
    headers = auth_headers(token)
    item = _create_watchlist_item(client, headers, "0050")
    _add_history("0050.TW", [50, 51, 52, 53, 54])

    insufficient = client.get(f"/api/stocks/watchlist/{item['id']}/indicators", headers=headers)
    assert insufficient.status_code == 200
    assert insufficient.json()["status"] == "insufficient_history"
    assert insufficient.json()["ma5"] == 52
    assert insufficient.json()["ma20"] is None
    assert insufficient.json()["rsi14"] is None

    empty_item = _create_watchlist_item(client, headers, "AAPL")
    empty = client.get(f"/api/stocks/watchlist/{empty_item['id']}/indicators", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["status"] == "no_price_history"
    assert empty.json()["latest_close"] is None


def test_indicator_api_is_user_scoped(client):
    token_a = register_and_login(client, "indicator-user-a@example.com")
    token_b = register_and_login(client, "indicator-user-b@example.com")
    item = _create_watchlist_item(client, auth_headers(token_a), "2330")

    response = client.get(f"/api/stocks/watchlist/{item['id']}/indicators", headers=auth_headers(token_b))

    assert response.status_code == 404


def test_rsi_edge_cases():
    assert calculate_rsi14([Decimal("10")] * 15) == Decimal("50.00")
    assert calculate_rsi14([Decimal(index) for index in range(1, 16)]) == Decimal("100.00")
    assert calculate_rsi14([Decimal(index) for index in range(15, 0, -1)]) == Decimal("0.00")


def test_create_list_and_validate_alerts(client):
    token = register_and_login(client, "alerts-create@example.com")
    headers = auth_headers(token)
    item = _create_watchlist_item(client, headers, "2330")

    invalid_condition = client.post(
        f"/api/stocks/watchlist/{item['id']}/alerts",
        headers=headers,
        json={"condition_type": "equal", "target_price": 1000},
    )
    assert invalid_condition.status_code == 422

    invalid_price = client.post(
        f"/api/stocks/watchlist/{item['id']}/alerts",
        headers=headers,
        json={"condition_type": "above", "target_price": 0},
    )
    assert invalid_price.status_code == 422

    created = client.post(
        f"/api/stocks/watchlist/{item['id']}/alerts",
        headers=headers,
        json={"condition_type": "above", "target_price": 1000},
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["symbol"] == "2330.TW"
    assert payload["target_price"] == 1000
    assert payload["is_active"] is True

    listed = client.get("/api/stocks/alerts", headers=headers)
    assert listed.status_code == 200
    assert [alert["id"] for alert in listed.json()] == [payload["id"]]


def test_alerts_are_user_scoped_for_update_and_delete(client):
    token_a = register_and_login(client, "alerts-user-a@example.com")
    token_b = register_and_login(client, "alerts-user-b@example.com")
    headers_a = auth_headers(token_a)
    headers_b = auth_headers(token_b)
    item = _create_watchlist_item(client, headers_a, "2330")
    alert = client.post(
        f"/api/stocks/watchlist/{item['id']}/alerts",
        headers=headers_a,
        json={"condition_type": "above", "target_price": 1000},
    ).json()

    assert client.get("/api/stocks/alerts", headers=headers_b).json() == []
    assert client.put(f"/api/stocks/alerts/{alert['id']}", headers=headers_b, json={"is_active": False}).status_code == 404
    assert client.delete(f"/api/stocks/alerts/{alert['id']}", headers=headers_b).status_code == 404


def test_alert_check_triggers_above_and_below_and_ignores_inactive(client):
    token = register_and_login(client, "alerts-check@example.com")
    headers = auth_headers(token)
    above_item = _create_watchlist_item(client, headers, "2330")
    below_item = _create_watchlist_item(client, headers, "0050")
    inactive_item = _create_watchlist_item(client, headers, "AAPL")
    _set_watchlist_price(above_item["id"], 1050)
    _set_watchlist_price(below_item["id"], 80)
    _set_watchlist_price(inactive_item["id"], 10)

    above = client.post(
        f"/api/stocks/watchlist/{above_item['id']}/alerts",
        headers=headers,
        json={"condition_type": "above", "target_price": 1000},
    ).json()
    below = client.post(
        f"/api/stocks/watchlist/{below_item['id']}/alerts",
        headers=headers,
        json={"condition_type": "below", "target_price": 100},
    ).json()
    inactive = client.post(
        f"/api/stocks/watchlist/{inactive_item['id']}/alerts",
        headers=headers,
        json={"condition_type": "above", "target_price": 5},
    ).json()
    client.put(f"/api/stocks/alerts/{inactive['id']}", headers=headers, json={"is_active": False})

    checked = client.post("/api/stocks/alerts/check", headers=headers)

    assert checked.status_code == 200
    payload = checked.json()
    assert payload["checked_count"] == 2
    assert payload["triggered_count"] == 2
    triggered_ids = {alert["id"] for alert in payload["alerts"]}
    assert triggered_ids == {above["id"], below["id"]}
    assert all(alert["is_active"] is False for alert in payload["alerts"])


def test_delete_alert(client):
    token = register_and_login(client, "alerts-delete@example.com")
    headers = auth_headers(token)
    item = _create_watchlist_item(client, headers, "2330")
    alert = client.post(
        f"/api/stocks/watchlist/{item['id']}/alerts",
        headers=headers,
        json={"condition_type": "below", "target_price": 900},
    ).json()

    deleted = client.delete(f"/api/stocks/alerts/{alert['id']}", headers=headers)

    assert deleted.status_code == 204
    assert client.get("/api/stocks/alerts", headers=headers).json() == []


def test_deleting_watchlist_item_removes_only_same_user_related_alerts(client):
    token_a = register_and_login(client, "alerts-delete-watchlist-a@example.com")
    token_b = register_and_login(client, "alerts-delete-watchlist-b@example.com")
    headers_a = auth_headers(token_a)
    headers_b = auth_headers(token_b)
    item_a = _create_watchlist_item(client, headers_a, "2330")
    item_b = _create_watchlist_item(client, headers_b, "2330")

    alert_a = client.post(
        f"/api/stocks/watchlist/{item_a['id']}/alerts",
        headers=headers_a,
        json={"condition_type": "above", "target_price": 1000},
    )
    alert_b = client.post(
        f"/api/stocks/watchlist/{item_b['id']}/alerts",
        headers=headers_b,
        json={"condition_type": "below", "target_price": 900},
    )
    assert alert_a.status_code == 201
    assert alert_b.status_code == 201

    deleted = client.delete(f"/api/stocks/watchlist/{item_a['id']}", headers=headers_a)

    assert deleted.status_code == 204
    assert client.get("/api/stocks/alerts", headers=headers_a).json() == []
    user_b_alerts = client.get("/api/stocks/alerts", headers=headers_b).json()
    assert len(user_b_alerts) == 1
    assert user_b_alerts[0]["id"] == alert_b.json()["id"]
