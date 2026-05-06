from __future__ import annotations

from datetime import date

from tests.conftest import auth_headers, register_and_login


def test_monthly_report_csv_export(client):
    token = register_and_login(client, "reports@example.com")
    month = date.today().strftime("%Y-%m")
    today = date.today().strftime("%Y-%m-%d")

    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 5000, "category": "Salary", "type": "income", "date": today, "note": "Payday"},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 1200, "category": "Food", "type": "expense", "date": today, "note": "Lunch"},
    )
    client.post(
        "/api/budgets",
        headers=auth_headers(token),
        json={"month": month, "category": "Food", "amount": 2000},
    )

    response = client.get(f"/api/reports/monthly?month={month}&format=csv", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "finance-report-" in response.headers["content-disposition"]
    assert response.content.startswith(b"\xef\xbb\xbf")
    text = response.content.decode("utf-8-sig")
    assert "Monthly Summary" in text
    assert "Budget Status" in text
    assert "Recent Transactions" in text
    assert "Food" in text


def test_monthly_report_pdf_export_empty_month(client):
    token = register_and_login(client, "reports-empty@example.com")
    response = client.get("/api/reports/monthly?month=2026-01&format=pdf", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_monthly_report_rejects_invalid_params(client):
    token = register_and_login(client, "reports-invalid@example.com")
    bad_month = client.get("/api/reports/monthly?month=2026/01&format=csv", headers=auth_headers(token))
    assert bad_month.status_code == 422

    bad_month_range = client.get("/api/reports/monthly?month=2026-99&format=csv", headers=auth_headers(token))
    assert bad_month_range.status_code == 422

    bad_format = client.get("/api/reports/monthly?month=2026-01&format=xlsx", headers=auth_headers(token))
    assert bad_format.status_code == 422


def test_monthly_report_is_user_scoped(client):
    token_a = register_and_login(client, "reports-a@example.com")
    token_b = register_and_login(client, "reports-b@example.com")
    month = date.today().strftime("%Y-%m")
    today = date.today().strftime("%Y-%m-%d")

    client.post(
        "/api/expenses",
        headers=auth_headers(token_a),
        json={"amount": 4321, "category": "Food", "type": "expense", "date": today, "note": "Only user A"},
    )

    response = client.get(f"/api/reports/monthly?month={month}&format=csv", headers=auth_headers(token_b))
    assert response.status_code == 200
    text = response.content.decode("utf-8-sig")
    assert "4321" not in text
