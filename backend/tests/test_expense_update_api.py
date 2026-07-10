from __future__ import annotations

from datetime import date

from tests.conftest import auth_headers, register_and_login


def _create_expense(client, token: str) -> int:
    response = client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 100, "category": "Food", "type": "expense", "date": "2026-07-01", "note": "Lunch"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_update_expense_success(client):
    token = register_and_login(client, "expense-update@example.com")
    expense_id = _create_expense(client, token)

    response = client.put(
        f"/api/expenses/{expense_id}",
        headers=auth_headers(token),
        json={"amount": 250.5, "category": "Salary", "type": "income", "date": "2026-07-02", "note": "Adjusted"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["amount"] == 250.5
    assert payload["category"] == "Salary"
    assert payload["type"] == "income"
    assert payload["date"] == date(2026, 7, 2).isoformat()
    assert payload["note"] == "Adjusted"


def test_update_expense_invalid_amount(client):
    token = register_and_login(client, "expense-invalid-amount@example.com")
    expense_id = _create_expense(client, token)

    response = client.put(
        f"/api/expenses/{expense_id}",
        headers=auth_headers(token),
        json={"amount": 0, "category": "Food", "type": "expense", "date": "2026-07-01"},
    )

    assert response.status_code == 422


def test_update_expense_invalid_type(client):
    token = register_and_login(client, "expense-invalid-type@example.com")
    expense_id = _create_expense(client, token)

    response = client.put(
        f"/api/expenses/{expense_id}",
        headers=auth_headers(token),
        json={"amount": 10, "category": "Food", "type": "transfer", "date": "2026-07-01"},
    )

    assert response.status_code == 422


def test_update_expense_cross_user_blocked(client):
    owner_token = register_and_login(client, "expense-owner@example.com")
    other_token = register_and_login(client, "expense-other@example.com")
    expense_id = _create_expense(client, owner_token)

    response = client.put(
        f"/api/expenses/{expense_id}",
        headers=auth_headers(other_token),
        json={"amount": 10, "category": "Food", "type": "expense", "date": "2026-07-01"},
    )

    assert response.status_code == 404


def test_update_expense_not_found(client):
    token = register_and_login(client, "expense-not-found@example.com")

    response = client.put(
        "/api/expenses/9999",
        headers=auth_headers(token),
        json={"amount": 10, "category": "Food", "type": "expense", "date": "2026-07-01"},
    )

    assert response.status_code == 404
