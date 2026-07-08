from __future__ import annotations

import re
import uuid
from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.expense import ExpenseCreate, ExpenseORM
from models.import_batch import (
    TransactionImportBatchORM,
    TransactionImportBatchResponse,
    TransactionImportNormalizedRow,
    TransactionImportPreviewResponse,
    TransactionImportPreviewRow,
    TransactionImportRowORM,
    TransactionImportSummary,
)
from models.user import UserORM
from parsers import parse_csv_rows, parse_excel_rows

FILE_SIZE_LIMIT_BYTES = 2 * 1024 * 1024
SUPPORTED_FILE_TYPES = {".csv": "csv", ".xlsx": "xlsx"}

HEADER_ALIASES = {
    "date": {"date", "transaction_date", "transaction date", "日期", "交易日期", "入帳日期", "消費日期", "付款日期", "交易日"},
    "amount": {"amount", "金額", "交易金額"},
    "type": {"type", "類型", "收支類型", "交易類型", "收支", "收入支出"},
    "category": {"category", "分類", "類別"},
    "note": {"description", "note", "memo", "摘要", "說明", "備註"},
    "payment_method": {"payment_method", "payment method", "支付方式", "付款方式"},
}

TYPE_ALIASES = {
    "expense": "expense",
    "spend": "expense",
    "debit": "expense",
    "支出": "expense",
    "消費": "expense",
    "income": "income",
    "credit": "income",
    "收入": "income",
    "入帳": "income",
}


def build_batch_response(batch: TransactionImportBatchORM) -> TransactionImportBatchResponse:
    summary = TransactionImportSummary(
        total_rows=batch.total_rows,
        valid_rows=batch.valid_rows,
        invalid_rows=batch.invalid_rows,
        duplicate_rows=batch.duplicate_rows,
        warning_rows=sum(1 for row in batch.rows if row.warnings),
        rows_to_import=sum(1 for row in batch.rows if row.status == "valid"),
        created_rows=batch.created_rows,
    )
    return TransactionImportBatchResponse(
        id=batch.id,
        file_name=batch.file_name,
        file_type=batch.file_type,
        total_rows=batch.total_rows,
        valid_rows=batch.valid_rows,
        invalid_rows=batch.invalid_rows,
        duplicate_rows=batch.duplicate_rows,
        created_rows=batch.created_rows,
        status=batch.status,
        created_at=batch.created_at,
        imported_at=batch.imported_at,
        summary=summary,
    )


def build_preview_row(row: TransactionImportRowORM) -> TransactionImportPreviewRow:
    normalized = TransactionImportNormalizedRow(
        transaction_date=row.normalized_date,
        amount=row.normalized_amount,
        type=row.normalized_type,
        category=row.normalized_category or "",
        description=row.normalized_note or "",
        payment_method=row.payment_method,
        source_file_name=row.batch.file_name,
        source_row_number=row.source_row_number,
        import_batch_id=row.batch_id,
    )
    return TransactionImportPreviewRow(
        id=row.id,
        source_row_number=row.source_row_number,
        raw_data=row.raw_data or {},
        normalized=normalized,
        status=row.status,
        validation_errors=list(row.validation_errors or []),
        warnings=list(row.warnings or []),
        duplicate_reasons=list(row.duplicate_reasons or []),
        created_expense_id=row.created_expense_id,
    )


def get_import_batch_or_404(db: Session, *, batch_id: str, user_id: int) -> TransactionImportBatchORM:
    batch = (
        db.query(TransactionImportBatchORM)
        .filter(TransactionImportBatchORM.id == batch_id, TransactionImportBatchORM.user_id == user_id)
        .first()
    )
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import batch not found.")
    return batch


def list_import_batches(db: Session, *, user: UserORM) -> list[TransactionImportBatchResponse]:
    batches = (
        db.query(TransactionImportBatchORM)
        .filter(TransactionImportBatchORM.user_id == user.id)
        .order_by(TransactionImportBatchORM.created_at.desc())
        .limit(20)
        .all()
    )
    return [build_batch_response(batch) for batch in batches]


def get_import_batch_detail(db: Session, *, batch_id: str, user: UserORM) -> TransactionImportPreviewResponse:
    batch = get_import_batch_or_404(db, batch_id=batch_id, user_id=user.id)
    return TransactionImportPreviewResponse(
        batch=build_batch_response(batch),
        rows=[build_preview_row(row) for row in batch.rows],
    )


def preview_transaction_import(
    db: Session,
    *,
    user: UserORM,
    file_name: str,
    content: bytes,
) -> TransactionImportPreviewResponse:
    file_type = _infer_file_type(file_name)
    if len(content) > FILE_SIZE_LIMIT_BYTES:
        raise HTTPException(status_code=413, detail="File is too large. Maximum size is 2 MB.")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        parsed_rows = _parse_rows(file_type=file_type, content=content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not parsed_rows:
        raise HTTPException(status_code=400, detail="The file contains no transaction rows.")

    header_map = _resolve_header_map(parsed_rows)
    batch = TransactionImportBatchORM(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_name=file_name,
        file_type=file_type,
        status="previewed",
    )
    db.add(batch)
    db.flush()

    normalized_records: list[dict[str, Any]] = []
    for index, row in enumerate(parsed_rows, start=2):
        normalized_records.append(_normalize_row(row=row, source_row_number=index, file_name=file_name, batch_id=batch.id, header_map=header_map))

    fingerprints = [record["fingerprint"] for record in normalized_records if record["fingerprint"]]
    file_duplicates = {fingerprint for fingerprint, count in Counter(fingerprints).items() if count > 1}
    database_duplicates = _find_database_duplicates(db, user_id=user.id, fingerprints=set(fingerprints))

    row_models: list[TransactionImportRowORM] = []
    for record in normalized_records:
        duplicate_reasons = list(record["duplicate_reasons"])
        fingerprint = record["fingerprint"]
        if fingerprint and fingerprint in file_duplicates:
            duplicate_reasons.append("duplicate_in_file")
        if fingerprint and fingerprint in database_duplicates:
            duplicate_reasons.append("duplicate_in_database")
        duplicate_reasons = sorted(set(duplicate_reasons))

        status_value = record["status"]
        if record["validation_errors"]:
            status_value = "invalid"
        elif duplicate_reasons:
            status_value = "duplicate"
        else:
            status_value = "valid"

        normalized = record["normalized"]
        row_models.append(
            TransactionImportRowORM(
                batch_id=batch.id,
                source_row_number=record["source_row_number"],
                raw_data=record["raw_data"],
                normalized_date=normalized["transaction_date"],
                normalized_amount=normalized["amount"],
                normalized_type=normalized["type"],
                normalized_category=normalized["category"],
                normalized_note=normalized["description"],
                payment_method=normalized["payment_method"],
                status=status_value,
                validation_errors=record["validation_errors"],
                warnings=record["warnings"],
                duplicate_reasons=duplicate_reasons,
                fingerprint=fingerprint,
            )
        )

    batch.rows = row_models
    batch.total_rows = len(row_models)
    batch.invalid_rows = sum(1 for row in row_models if row.status == "invalid")
    batch.duplicate_rows = sum(1 for row in row_models if row.status == "duplicate")
    batch.valid_rows = sum(1 for row in row_models if row.status == "valid")
    db.commit()
    db.refresh(batch)

    return TransactionImportPreviewResponse(
        batch=build_batch_response(batch),
        rows=[build_preview_row(row) for row in batch.rows],
    )


def confirm_transaction_import(
    db: Session,
    *,
    user: UserORM,
    batch_id: str,
    selected_row_numbers: list[int] | None,
) -> dict[str, Any]:
    batch = get_import_batch_or_404(db, batch_id=batch_id, user_id=user.id)
    if batch.status == "imported":
        raise HTTPException(status_code=409, detail="This import batch has already been confirmed.")

    rows = batch.rows
    if selected_row_numbers == []:
        raise HTTPException(status_code=400, detail="Select at least one valid row to import.")
    if selected_row_numbers is None:
        rows = [row for row in rows if row.status == "valid"]
    else:
        selected_set = set(selected_row_numbers)
        rows = [row for row in rows if row.source_row_number in selected_set]

    created_ids: list[int] = []
    skipped_count = 0
    duplicate_count = 0
    error_count = 0

    for row in rows:
        if row.status == "duplicate":
            skipped_count += 1
            duplicate_count += 1
            continue
        if row.status != "valid":
            skipped_count += 1
            error_count += 1
            continue
        try:
            payload = ExpenseCreate(
                amount=row.normalized_amount,
                category=row.normalized_category,
                type=row.normalized_type,
                date=row.normalized_date,
                note=row.normalized_note,
            )
            expense = ExpenseORM(
                user_id=user.id,
                amount=payload.amount,
                category=payload.category,
                type=payload.type,
                date=payload.date,
                note=payload.note,
            )
            db.add(expense)
            db.flush()
            row.created_expense_id = expense.id
            created_ids.append(expense.id)
        except Exception:
            skipped_count += 1
            error_count += 1

    batch.created_rows = len(created_ids)
    batch.status = "imported"
    batch.imported_at = datetime.now()
    db.commit()

    return {
        "batch_id": batch.id,
        "created_count": len(created_ids),
        "skipped_count": skipped_count,
        "duplicate_count": duplicate_count,
        "error_count": error_count,
        "created_transaction_ids": created_ids,
    }


def _infer_file_type(file_name: str) -> str:
    normalized = str(file_name or "").strip().lower()
    for suffix, file_type in SUPPORTED_FILE_TYPES.items():
        if normalized.endswith(suffix):
            return file_type
    raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a CSV or XLSX file.")


def _parse_rows(*, file_type: str, content: bytes) -> list[dict[str, Any]]:
    if file_type == "csv":
        return parse_csv_rows(content)
    if file_type == "xlsx":
        return parse_excel_rows(content)
    raise ValueError("Unsupported file type.")


def _resolve_header_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    first_row = rows[0] if rows else {}
    normalized_headers = {key: _normalize_header_name(key) for key in first_row.keys()}
    mapping: dict[str, str] = {}
    for target, aliases in HEADER_ALIASES.items():
        for raw_header, normalized_header in normalized_headers.items():
            if normalized_header in aliases:
                mapping[target] = raw_header
                break

    missing_required = [field for field in ("date", "amount", "category") if field not in mapping]
    if missing_required:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_required)}.",
        )
    return mapping


def _normalize_header_name(value: Any) -> str:
    return re.sub(r"[\s\-]+", "_", str(value or "").strip().lower())


def _normalize_row(*, row: dict[str, Any], source_row_number: int, file_name: str, batch_id: str, header_map: dict[str, str]) -> dict[str, Any]:
    validation_errors: list[str] = []
    warnings: list[str] = []
    duplicate_reasons: list[str] = []

    date_value = row.get(header_map.get("date", ""))
    amount_value = row.get(header_map.get("amount", ""))
    type_value = row.get(header_map.get("type", "")) if "type" in header_map else None
    category_value = row.get(header_map.get("category", ""))
    note_value = row.get(header_map.get("note", "")) if "note" in header_map else None
    payment_method_value = row.get(header_map.get("payment_method", "")) if "payment_method" in header_map else None

    normalized_date = _parse_date_value(date_value)
    if normalized_date is None:
        validation_errors.append("Invalid transaction date.")

    parsed_amount = _parse_amount_value(amount_value)
    if parsed_amount is None:
        validation_errors.append("Invalid amount.")

    normalized_type = _parse_type_value(type_value)
    normalized_category = str(category_value or "").strip()
    if not normalized_category:
        validation_errors.append("Category is required.")
    elif len(normalized_category) > 50:
        validation_errors.append("Category must be 50 characters or fewer.")

    note = str(note_value or "").strip() or None
    if note and len(note) > 500:
        warnings.append("Note was truncated to 500 characters.")
        note = note[:500].rstrip()

    payment_method = str(payment_method_value or "").strip() or None
    if payment_method and len(payment_method) > 100:
        warnings.append("Payment method was truncated to 100 characters.")
        payment_method = payment_method[:100].rstrip()

    amount_abs: Decimal | None = None
    if parsed_amount is not None:
        amount_abs = abs(parsed_amount)
        if amount_abs == 0:
            validation_errors.append("Amount must be greater than 0.")

    if normalized_type is None and parsed_amount is not None:
        normalized_type = "expense"
        warnings.append("Type was not provided. Defaulted to expense.")

    normalized = {
        "transaction_date": normalized_date,
        "amount": amount_abs,
        "type": normalized_type,
        "category": normalized_category,
        "description": note or "",
        "payment_method": payment_method,
    }
    fingerprint = _build_fingerprint(
        transaction_date=normalized_date,
        amount=amount_abs,
        category=normalized_category,
        note=note,
    )
    if normalized_type == "income" and parsed_amount is not None and parsed_amount < 0:
        warnings.append("Negative income amount was converted to a positive stored value.")

    status_value = "valid" if not validation_errors else "invalid"
    return {
        "source_row_number": source_row_number,
        "raw_data": {str(key): _serialize_raw_value(value) for key, value in row.items()},
        "normalized": normalized,
        "validation_errors": validation_errors,
        "warnings": sorted(set(warnings)),
        "duplicate_reasons": duplicate_reasons,
        "fingerprint": fingerprint,
        "status": status_value,
    }


def _serialize_raw_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _parse_date_value(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return (datetime(1899, 12, 30) + timedelta(days=float(value))).date()
        except (OverflowError, ValueError):
            return None

    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount_value(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Decimal(str(value))

    text = str(value).strip()
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    sanitized = text.replace(",", "").replace("(", "").replace(")", "")
    try:
        amount = Decimal(sanitized)
    except InvalidOperation:
        return None
    return -amount if negative else amount


def _parse_type_value(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    return TYPE_ALIASES.get(text)


def _build_fingerprint(*, transaction_date: date | None, amount: Decimal | None, category: str, note: str | None) -> str | None:
    if transaction_date is None or amount is None or not category.strip():
        return None
    normalized_note = re.sub(r"\s+", " ", (note or "").strip().lower())
    normalized_category = re.sub(r"\s+", " ", category.strip().lower())
    return f"{transaction_date.isoformat()}|{amount:.2f}|{normalized_category}|{normalized_note}"


def _find_database_duplicates(db: Session, *, user_id: int, fingerprints: set[str]) -> set[str]:
    if not fingerprints:
        return set()
    matches: set[str] = set()
    expenses = db.query(ExpenseORM).filter(ExpenseORM.user_id == user_id).all()
    for expense in expenses:
        fingerprint = _build_fingerprint(
            transaction_date=expense.date,
            amount=Decimal(str(expense.amount)),
            category=expense.category,
            note=expense.note,
        )
        if fingerprint in fingerprints:
            matches.add(fingerprint)
    return matches
