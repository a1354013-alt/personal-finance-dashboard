from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from tests.conftest import auth_headers, register_and_login


def make_csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def make_xlsx_bytes(rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def preview_import(client, token: str, *, file_name: str, content: bytes):
    return client.post(
        "/api/imports/transactions/preview",
        headers=auth_headers(token),
        files={"file": (file_name, content)},
    )


def test_preview_valid_csv(client):
    token = register_and_login(client, "import-csv@example.com")
    content = make_csv_bytes(
        "date,amount,type,category,note\n"
        "2026-07-01,125.50,expense,Food,Lunch\n"
        "2026/07/02,2500,income,Salary,Payroll\n"
    )

    response = preview_import(client, token, file_name="transactions.csv", content=content)

    assert response.status_code == 201
    payload = response.json()
    assert payload["batch"]["file_type"] == "csv"
    assert payload["batch"]["summary"]["total_rows"] == 2
    assert payload["batch"]["summary"]["rows_to_import"] == 2
    assert payload["rows"][0]["normalized"]["transaction_date"] == "2026-07-01"
    assert payload["rows"][0]["normalized"]["amount"] == 125.5
    assert payload["rows"][1]["normalized"]["type"] == "income"


def test_preview_csv_accepts_additional_chinese_column_aliases(client):
    token = register_and_login(client, "import-zh-aliases@example.com")
    content = make_csv_bytes(
        "消費日期,金額,收支,分類,備註\n"
        "2026-07-01,125.50,支出,餐飲,午餐\n"
        "2026-07-02,2500,收入,薪資,兼職\n"
    )

    response = preview_import(client, token, file_name="transactions.csv", content=content)

    assert response.status_code == 201
    rows = response.json()["rows"]
    assert rows[0]["normalized"]["transaction_date"] == "2026-07-01"
    assert rows[0]["normalized"]["type"] == "expense"
    assert rows[1]["normalized"]["transaction_date"] == "2026-07-02"
    assert rows[1]["normalized"]["type"] == "income"


def test_preview_csv_accepts_payment_date_transaction_day_and_income_expense_aliases(client):
    token = register_and_login(client, "import-zh-date-type-aliases@example.com")
    payment_date_content = make_csv_bytes(
        "付款日期,金額,收入支出,分類\n"
        "2026-07-03,88,支出,交通\n"
    )
    transaction_day_content = make_csv_bytes(
        "交易日,金額,收入支出,分類\n"
        "2026-07-04,3000,收入,獎金\n"
    )

    payment_date_response = preview_import(client, token, file_name="payment-date.csv", content=payment_date_content)
    transaction_day_response = preview_import(client, token, file_name="transaction-day.csv", content=transaction_day_content)

    assert payment_date_response.status_code == 201
    assert payment_date_response.json()["rows"][0]["normalized"]["transaction_date"] == "2026-07-03"
    assert payment_date_response.json()["rows"][0]["normalized"]["type"] == "expense"
    assert transaction_day_response.status_code == 201
    assert transaction_day_response.json()["rows"][0]["normalized"]["transaction_date"] == "2026-07-04"
    assert transaction_day_response.json()["rows"][0]["normalized"]["type"] == "income"


def test_preview_valid_xlsx(client):
    token = register_and_login(client, "import-xlsx@example.com")
    content = make_xlsx_bytes(
        [
            ["date", "amount", "type", "category", "note"],
            [45474, 980, "expense", "Transport", "Taxi"],
            ["20260704", 5000, "income", "Salary", "Bonus"],
        ]
    )

    response = preview_import(client, token, file_name="transactions.xlsx", content=content)

    assert response.status_code == 201
    payload = response.json()
    assert payload["batch"]["file_type"] == "xlsx"
    assert payload["rows"][0]["normalized"]["transaction_date"] == "2024-07-01"
    assert payload["rows"][1]["normalized"]["transaction_date"] == "2026-07-04"


def test_reject_unsupported_file_type(client):
    token = register_and_login(client, "import-badtype@example.com")

    response = preview_import(client, token, file_name="transactions.txt", content=b"hello")

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_reject_empty_file(client):
    token = register_and_login(client, "import-empty@example.com")

    response = preview_import(client, token, file_name="transactions.csv", content=b"")

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."


def test_row_level_validation_for_invalid_date_and_amount(client):
    token = register_and_login(client, "import-invalid@example.com")
    content = make_csv_bytes(
        "date,amount,category,note\n"
        "2026-99-01,abc,Food,Bad row\n"
    )

    response = preview_import(client, token, file_name="transactions.csv", content=content)

    assert response.status_code == 201
    row = response.json()["rows"][0]
    assert row["status"] == "invalid"
    assert "Invalid transaction date." in row["validation_errors"]
    assert "Invalid amount." in row["validation_errors"]


def test_duplicate_detection_inside_uploaded_file(client):
    token = register_and_login(client, "import-dup-file@example.com")
    content = make_csv_bytes(
        "date,amount,category,note\n"
        "2026-07-01,120,Food,Coffee\n"
        "2026-07-01,120,Food,Coffee\n"
    )

    response = preview_import(client, token, file_name="transactions.csv", content=content)

    assert response.status_code == 201
    payload = response.json()
    assert payload["batch"]["summary"]["duplicate_rows"] == 2
    assert all("duplicate_in_file" in row["duplicate_reasons"] for row in payload["rows"])


def test_duplicate_detection_against_existing_database_rows(client):
    token = register_and_login(client, "import-dup-db@example.com")
    create_response = client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 120, "category": "Food", "type": "expense", "date": "2026-07-01", "note": "Coffee"},
    )
    assert create_response.status_code == 201

    content = make_csv_bytes(
        "date,amount,category,note\n"
        "2026-07-01,120,Food,Coffee\n"
    )
    response = preview_import(client, token, file_name="transactions.csv", content=content)

    assert response.status_code == 201
    row = response.json()["rows"][0]
    assert row["status"] == "duplicate"
    assert row["duplicate_reasons"] == ["duplicate_in_database"]


def test_confirm_import_creates_valid_rows_and_skips_invalid_or_duplicates(client):
    token = register_and_login(client, "import-confirm@example.com")
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 120, "category": "Food", "type": "expense", "date": "2026-07-01", "note": "Coffee"},
    )
    content = make_csv_bytes(
        "date,amount,type,category,note\n"
        "2026-07-02,88,expense,Food,Tea\n"
        "2026-07-01,120,expense,Food,Coffee\n"
        "bad-date,50,expense,Food,Oops\n"
    )

    preview = preview_import(client, token, file_name="transactions.csv", content=content)
    batch_id = preview.json()["batch"]["id"]
    selected_row_numbers = [row["source_row_number"] for row in preview.json()["rows"]]

    confirm = client.post(
        f"/api/imports/transactions/{batch_id}/confirm",
        headers=auth_headers(token),
        json={"selected_row_numbers": selected_row_numbers},
    )

    assert confirm.status_code == 200
    payload = confirm.json()
    assert payload["created_count"] == 1
    assert payload["duplicate_count"] == 1
    assert payload["error_count"] == 1

    expenses = client.get("/api/expenses", headers=auth_headers(token))
    assert expenses.status_code == 200
    assert len(expenses.json()) == 2


def test_confirm_import_with_null_selected_rows_imports_all_valid_rows_only(client):
    token = register_and_login(client, "import-null-selected@example.com")
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 120, "category": "Food", "type": "expense", "date": "2026-07-01", "note": "Coffee"},
    )
    content = make_csv_bytes(
        "date,amount,type,category,note\n"
        "2026-07-02,88,expense,Food,Tea\n"
        "2026-07-01,120,expense,Food,Coffee\n"
        "bad-date,50,expense,Food,Oops\n"
    )
    preview = preview_import(client, token, file_name="transactions.csv", content=content)
    batch_id = preview.json()["batch"]["id"]

    confirm = client.post(
        f"/api/imports/transactions/{batch_id}/confirm",
        headers=auth_headers(token),
        json={"selected_row_numbers": None},
    )

    assert confirm.status_code == 200
    payload = confirm.json()
    assert payload["created_count"] == 1
    assert payload["skipped_count"] == 0
    assert payload["duplicate_count"] == 0
    assert payload["error_count"] == 0


def test_confirm_import_with_empty_selected_rows_returns_clear_400(client):
    token = register_and_login(client, "import-empty-selected@example.com")
    preview = preview_import(
        client,
        token,
        file_name="transactions.csv",
        content=make_csv_bytes("date,amount,type,category,note\n2026-07-02,88,expense,Food,Tea\n"),
    )
    batch_id = preview.json()["batch"]["id"]

    confirm = client.post(
        f"/api/imports/transactions/{batch_id}/confirm",
        headers=auth_headers(token),
        json={"selected_row_numbers": []},
    )

    assert confirm.status_code == 400
    assert confirm.json()["detail"] == "Select at least one valid row to import."


def test_confirm_import_with_selected_rows(client):
    token = register_and_login(client, "import-selected@example.com")
    content = make_csv_bytes(
        "date,amount,type,category,note\n"
        "2026-07-02,88,expense,Food,Tea\n"
        "2026-07-03,50,expense,Transport,Metro\n"
    )
    preview = preview_import(client, token, file_name="transactions.csv", content=content)
    batch_id = preview.json()["batch"]["id"]
    second_row_number = preview.json()["rows"][1]["source_row_number"]

    confirm = client.post(
        f"/api/imports/transactions/{batch_id}/confirm",
        headers=auth_headers(token),
        json={"selected_row_numbers": [second_row_number]},
    )

    assert confirm.status_code == 200
    assert confirm.json()["created_count"] == 1

    expenses = client.get("/api/expenses", headers=auth_headers(token)).json()
    assert len(expenses) == 1
    assert expenses[0]["note"] == "Metro"


def test_user_cannot_access_another_users_import_batch(client):
    token_a = register_and_login(client, "import-a@example.com")
    token_b = register_and_login(client, "import-b@example.com")
    preview = preview_import(
        client,
        token_a,
        file_name="transactions.csv",
        content=make_csv_bytes("date,amount,category\n2026-07-01,120,Food\n"),
    )
    batch_id = preview.json()["batch"]["id"]

    detail = client.get(f"/api/imports/transactions/{batch_id}", headers=auth_headers(token_b))
    confirm = client.post(
        f"/api/imports/transactions/{batch_id}/confirm",
        headers=auth_headers(token_b),
        json={},
    )

    assert detail.status_code == 404
    assert confirm.status_code == 404


def test_import_batch_summary_and_listing_are_correct(client):
    token = register_and_login(client, "import-list@example.com")
    preview = preview_import(
        client,
        token,
        file_name="transactions.csv",
        content=make_csv_bytes(
            "date,amount,category,note\n"
            "2026-07-01,120,Food,Coffee\n"
            "bad-date,33,Food,Bad row\n"
        ),
    )
    batch_id = preview.json()["batch"]["id"]

    detail = client.get(f"/api/imports/transactions/{batch_id}", headers=auth_headers(token))
    listing = client.get("/api/imports/transactions", headers=auth_headers(token))

    assert detail.status_code == 200
    assert detail.json()["batch"]["summary"]["valid_rows"] == 1
    assert detail.json()["batch"]["summary"]["invalid_rows"] == 1
    assert listing.status_code == 200
    assert listing.json()[0]["id"] == batch_id
    assert listing.json()[0]["summary"]["rows_to_import"] == 1
