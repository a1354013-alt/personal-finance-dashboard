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


def test_generate_current_month_creates_transactions_once(client):
    token = register_and_login(client, "recurring-generate@example.com")
    item = _create(client, token, amount=450, category="Utilities", note="Monthly bill")

    first = client.post("/api/recurring-transactions/generate-current-month", headers=auth_headers(token))
    second = client.post("/api/recurring-transactions/generate-current-month", headers=auth_headers(token))
    expenses = client.get("/api/expenses", headers=auth_headers(token))
    occurrences = client.get("/api/recurring-transactions/occurrences", headers=auth_headers(token))

    assert first.status_code == 200
    assert first.json()["created_count"] == 1
    assert second.status_code == 200
    assert second.json()["already_existing_count"] == 1
    assert len(expenses.json()) == 1
    assert expenses.json()[0]["category"] == "Utilities"
    assert occurrences.status_code == 200
    assert occurrences.json()[0]["recurring_transaction_id"] == item["id"]
    assert occurrences.json()[0]["status"] == "generated"


def test_generate_current_month_skips_inactive_and_ended_recurring(client):
    token = register_and_login(client, "recurring-generate-inactive@example.com")
    active = _create(client, token, amount=300, category="Food", note="Meal plan")
    inactive = _create(client, token, amount=700, category="Travel", note="Paused travel")
    client.patch(f"/api/recurring-transactions/{inactive['id']}/deactivate", headers=auth_headers(token))
    _create(
        client,
        token,
        amount=500,
        category="Housing",
        note="Expired",
        start_date="2026-01-01",
        end_date="2026-01-01",
    )

    response = client.post("/api/recurring-transactions/generate-current-month", headers=auth_headers(token))
    expenses = client.get("/api/expenses", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["created_count"] == 1
    assert len(expenses.json()) == 1
    assert expenses.json()[0]["category"] == "Food"
    assert expenses.json()[0]["note"] == "Meal plan"


def test_generate_occurrence_and_skip_are_user_scoped(client):
    token = register_and_login(client, "recurring-occurrence-owner@example.com")
    other_token = register_and_login(client, "recurring-occurrence-other@example.com")
    _create(client, token, amount=220, category="Shopping", note="Subscription")
    occurrences = client.get("/api/recurring-transactions/occurrences", headers=auth_headers(token))
    occurrence_id = occurrences.json()[0]["id"]

    generate_response = client.post(
        f"/api/recurring-transactions/occurrences/{occurrence_id}/generate",
        headers=auth_headers(other_token),
    )
    skip_response = client.post(
        f"/api/recurring-transactions/occurrences/{occurrence_id}/skip",
        headers=auth_headers(other_token),
    )

    assert generate_response.status_code == 404
    assert skip_response.status_code == 404


def test_skip_occurrence_updates_status_without_creating_transaction(client):
    token = register_and_login(client, "recurring-skip-occurrence@example.com")
    _create(client, token, amount=120, category="Entertainment", note="Streaming")
    occurrences = client.get("/api/recurring-transactions/occurrences", headers=auth_headers(token))
    occurrence_id = occurrences.json()[0]["id"]

    response = client.post(
        f"/api/recurring-transactions/occurrences/{occurrence_id}/skip",
        headers=auth_headers(token),
    )
    updated_occurrences = client.get("/api/recurring-transactions/occurrences", headers=auth_headers(token))
    expenses = client.get("/api/expenses", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["summary"]["skipped_count"] == 1
    assert updated_occurrences.json()[0]["status"] == "skipped"
    assert expenses.json() == []


def test_list_occurrences_accepts_valid_month_query(client):
    token = register_and_login(client, "recurring-occurrences-valid-month@example.com")

    response = client.get("/api/recurring-transactions/occurrences?month=2026-07", headers=auth_headers(token))

    assert response.status_code == 200


def test_list_occurrences_rejects_invalid_month_string(client):
    token = register_and_login(client, "recurring-occurrences-invalid-string@example.com")

    response = client.get("/api/recurring-transactions/occurrences?month=2026/07", headers=auth_headers(token))

    assert response.status_code == 422


def test_list_occurrences_rejects_invalid_month_number(client):
    token = register_and_login(client, "recurring-occurrences-invalid-number@example.com")

    response = client.get("/api/recurring-transactions/occurrences?month=2026-13", headers=auth_headers(token))

    assert response.status_code == 422
