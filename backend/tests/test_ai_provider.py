from __future__ import annotations

import os
from datetime import date

import pytest

from providers.llm.factory import reset_llm_provider_cache


def register_and_login(client, email: str) -> str:
    register_response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert register_response.status_code == 201
    login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_ai_falls_back_when_openai_missing_key(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    reset_llm_provider_cache()

    token = register_and_login(client, "ai-fallback@example.com")
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 1000, "category": "Salary", "type": "income", "date": "2026-04-01", "note": "Salary"},
    )

    response = client.get("/api/ai/summary", headers=auth_headers(token))
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["provider"] == "fallback"
    assert payload["meta"]["is_fallback"] is True


def test_ai_uses_mock_provider_in_tests(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MOCK_TEXT", "hello from mock")
    reset_llm_provider_cache()

    token = register_and_login(client, "ai-mock@example.com")
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 1000, "category": "Salary", "type": "income", "date": "2026-04-01", "note": "Salary"},
    )

    response = client.get("/api/ai/summary", headers=auth_headers(token))
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == "hello from mock"
    assert payload["meta"]["provider"] == "mock"
    assert payload["meta"]["is_fallback"] is False


def test_ai_openai_runtime_error_degrades_to_fallback(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.invalid")
    reset_llm_provider_cache()

    # Force requests.post to time out deterministically.
    import providers.llm.openai_provider as openai_provider
    import requests

    def _timeout(*_args, **_kwargs):
        raise requests.Timeout("boom")

    monkeypatch.setattr(openai_provider.requests, "post", _timeout)

    token = register_and_login(client, "ai-openai-timeout@example.com")
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 1000, "category": "Salary", "type": "income", "date": "2026-04-01", "note": "Salary"},
    )

    response = client.get("/api/ai/summary", headers=auth_headers(token))
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["provider"] == "fallback"
    assert payload["meta"]["is_fallback"] is True
    assert payload["meta"]["error"]


def test_ai_summary_handles_decimal_expense_amounts(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MOCK_TEXT", "decimal summary")
    reset_llm_provider_cache()

    token = register_and_login(client, "ai-decimal-expense@example.com")
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 1000, "category": "Salary", "type": "income", "date": "2026-05-01", "note": "Salary"},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 123.45, "category": "Food", "type": "expense", "date": "2026-05-15", "note": "Groceries"},
    )

    response = client.get("/api/ai/summary", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["summary"] == "decimal summary"


def test_budget_advice_marks_over_budget_items(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MOCK_TEXT", "budget advice")
    reset_llm_provider_cache()

    month = date.today().strftime("%Y-%m")
    day = date.today().strftime("%Y-%m-%d")
    token = register_and_login(client, "ai-budget-over@example.com")
    headers = auth_headers(token)
    client.post(
        "/api/budgets",
        headers=headers,
        json={"month": month, "category": "Food", "amount": 100},
    )
    client.post(
        "/api/expenses",
        headers=headers,
        json={"amount": 120, "category": "Food", "type": "expense", "date": day, "note": "Groceries"},
    )

    response = client.get("/api/ai/budget-advice", headers=headers)
    assert response.status_code == 200
    item = response.json()["budget_status"][0]
    assert item["over_budget"] is True
    assert item["warning"] is False


def test_budget_advice_empty_state_is_json_serializable(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "fallback")
    reset_llm_provider_cache()

    token = register_and_login(client, "ai-budget-empty@example.com")

    response = client.get("/api/ai/budget-advice", headers=auth_headers(token))
    assert response.status_code == 200
    payload = response.json()
    assert payload["budget_status"] == []
    assert "No budgets have been created yet" in payload["advice"]

