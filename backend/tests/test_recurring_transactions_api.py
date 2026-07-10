from __future__ import annotations

from tests.conftest import auth_headers, register_and_login


def _payload(**overrides):
    payload = {
        "amount": 1200,
        "category": "Housing",
        "type": "expense",
        "note": "Rent",
        "frequency": "monthly",
        "start_date": "2026-07-01",
        "end_date": None,
    }
    payload.update(overrides)
    return payload


def _create(client, token: str, **overrides) -> dict:
    response = client.post("/api/recurring-transactions", headers=auth_headers(token), json=_payload(**overrides))
    assert response.status_code == 201
    return response.json()


def test_create_recurring_transaction(client):
    token = register_and_login(client, "recurring-create@example.com")

    payload = _create(client, token)

    assert payload["category"] == "Housing"
    assert payload["frequency"] == "monthly"
    assert payload["is_active"] is True
    assert payload["next_run_date"] is not None


def test_list_recurring_transactions_current_user_only(client):
    token = register_and_login(client, "recurring-list@example.com")
    other_token = register_and_login(client, "recurring-list-other@example.com")
    _create(client, token, category="Housing")
    _create(client, other_token, category="Food")

    response = client.get("/api/recurring-transactions", headers=auth_headers(token))

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["category"] == "Housing"


def test_update_recurring_transaction(client):
    token = register_and_login(client, "recurring-update@example.com")
    item = _create(client, token)

    response = client.put(
        f"/api/recurring-transactions/{item['id']}",
        headers=auth_headers(token),
        json=_payload(amount=1500, category="Utilities", frequency="weekly", is_active=True),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["amount"] == 1500
    assert payload["category"] == "Utilities"
    assert payload["frequency"] == "weekly"


def test_deactivate_recurring_transaction(client):
    token = register_and_login(client, "recurring-deactivate@example.com")
    item = _create(client, token)

    response = client.patch(f"/api/recurring-transactions/{item['id']}/deactivate", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["next_run_date"] is None


def test_delete_recurring_transaction(client):
    token = register_and_login(client, "recurring-delete@example.com")
    item = _create(client, token)

    delete_response = client.delete(f"/api/recurring-transactions/{item['id']}", headers=auth_headers(token))
    list_response = client.get("/api/recurring-transactions", headers=auth_headers(token))

    assert delete_response.status_code == 204
    assert list_response.json() == []


def test_recurring_invalid_frequency(client):
    token = register_and_login(client, "recurring-invalid-frequency@example.com")

    response = client.post("/api/recurring-transactions", headers=auth_headers(token), json=_payload(frequency="daily"))

    assert response.status_code == 422


def test_recurring_invalid_amount(client):
    token = register_and_login(client, "recurring-invalid-amount@example.com")

    response = client.post("/api/recurring-transactions", headers=auth_headers(token), json=_payload(amount=-1))

    assert response.status_code == 422


def test_recurring_cross_user_access_blocked(client):
    owner_token = register_and_login(client, "recurring-owner@example.com")
    other_token = register_and_login(client, "recurring-other@example.com")
    item = _create(client, owner_token)

    response = client.put(
        f"/api/recurring-transactions/{item['id']}",
        headers=auth_headers(other_token),
        json=_payload(amount=999, is_active=True),
    )

    assert response.status_code == 404
