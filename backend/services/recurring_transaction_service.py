from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from models.expense import ExpenseORM
from models.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionGenerationSummary,
    RecurringTransactionOccurrenceORM,
    RecurringTransactionUpdate,
    RecurringTransactionORM,
)


def add_months(value: date, months: int) -> date:
    target_month_index = value.year * 12 + (value.month - 1) + months
    target_year = target_month_index // 12
    target_month = (target_month_index % 12) + 1
    return date(target_year, target_month, min(value.day, monthrange(target_year, target_month)[1]))


def advance_date(value: date, frequency: str) -> date:
    if frequency == "weekly":
        return value + timedelta(days=7)
    if frequency == "yearly":
        return add_months(value, 12)
    return add_months(value, 1)


def derive_next_run_date(start_date: date, frequency: str, end_date: date | None, *, today: date | None = None) -> date | None:
    current = start_date
    today = today or date.today()
    while current < today:
        current = advance_date(current, frequency)
    if end_date and current > end_date:
        return None
    return current


def pending_occurrences_until(recurring: RecurringTransactionORM, end_date: date, *, today: date | None = None) -> list[date]:
    if not recurring.is_active:
        return []
    today = today or date.today()
    current = recurring.next_run_date
    if current is None or current < today:
        current = derive_next_run_date(recurring.start_date, recurring.frequency, recurring.end_date, today=today)
    if current is None:
        return []
    dates: list[date] = []
    while current and current <= end_date:
        if recurring.end_date and current > recurring.end_date:
            break
        if current >= today:
            dates.append(current)
        current = advance_date(current, recurring.frequency)
    return dates


def month_bounds(target: date | None = None) -> tuple[date, date]:
    target = target or date.today()
    month_start = target.replace(day=1)
    month_end = target.replace(day=monthrange(target.year, target.month)[1])
    return month_start, month_end


def scheduled_occurrences_between(recurring: RecurringTransactionORM, start_date: date, end_date: date) -> list[date]:
    if not recurring.is_active:
        return []
    current = recurring.start_date
    dates: list[date] = []
    while current < start_date:
        current = advance_date(current, recurring.frequency)
    while current <= end_date:
        if recurring.end_date and current > recurring.end_date:
            break
        dates.append(current)
        current = advance_date(current, recurring.frequency)
    return dates


def ensure_occurrence_records_for_month(
    db: Session,
    *,
    recurring: RecurringTransactionORM,
    target_date: date | None = None,
) -> list[RecurringTransactionOccurrenceORM]:
    if not recurring.is_active:
        return []

    month_start, month_end = month_bounds(target_date)
    scheduled_dates = scheduled_occurrences_between(recurring, month_start, month_end)
    if not scheduled_dates:
        recurring.next_run_date = recalculate_next_run_date(db, recurring, today=target_date or date.today())
        return []

    existing_rows = (
        db.query(RecurringTransactionOccurrenceORM)
        .filter(
            RecurringTransactionOccurrenceORM.recurring_transaction_id == recurring.id,
            RecurringTransactionOccurrenceORM.scheduled_date >= month_start,
            RecurringTransactionOccurrenceORM.scheduled_date <= month_end,
        )
        .all()
    )
    existing_by_date = {row.scheduled_date: row for row in existing_rows}

    created_rows: list[RecurringTransactionOccurrenceORM] = []
    for scheduled_date in scheduled_dates:
        if scheduled_date in existing_by_date:
            continue
        row = RecurringTransactionOccurrenceORM(
            recurring_transaction_id=recurring.id,
            user_id=recurring.user_id,
            scheduled_date=scheduled_date,
            status="pending",
        )
        db.add(row)
        created_rows.append(row)

    if created_rows:
        db.flush()
        existing_rows.extend(created_rows)

    recurring.next_run_date = recalculate_next_run_date(db, recurring, today=target_date or date.today())
    return sorted(existing_rows, key=lambda row: row.scheduled_date)


def ensure_occurrences_for_user_month(
    db: Session,
    *,
    user_id: int,
    target_date: date | None = None,
) -> list[RecurringTransactionOccurrenceORM]:
    recurrences = (
        db.query(RecurringTransactionORM)
        .filter(
            RecurringTransactionORM.user_id == user_id,
            RecurringTransactionORM.is_active.is_(True),
        )
        .all()
    )
    all_rows: list[RecurringTransactionOccurrenceORM] = []
    for recurring in recurrences:
        all_rows.extend(ensure_occurrence_records_for_month(db, recurring=recurring, target_date=target_date))
    db.flush()
    return all_rows


def recalculate_next_run_date(db: Session, recurring: RecurringTransactionORM, *, today: date | None = None) -> date | None:
    if not recurring.is_active:
        return None

    today = today or date.today()
    current = derive_next_run_date(recurring.start_date, recurring.frequency, recurring.end_date, today=today)
    if current is None:
        return None

    while current is not None:
        occurrence = (
            db.query(RecurringTransactionOccurrenceORM)
            .filter(
                RecurringTransactionOccurrenceORM.recurring_transaction_id == recurring.id,
                RecurringTransactionOccurrenceORM.scheduled_date == current,
            )
            .first()
        )
        if occurrence is None or occurrence.status == "pending":
            return current
        current = advance_date(current, recurring.frequency)
        if recurring.end_date and current > recurring.end_date:
            return None
    return None


def create_recurring_transaction(
    db: Session,
    *,
    user_id: int,
    payload: RecurringTransactionCreate,
) -> RecurringTransactionORM:
    item = RecurringTransactionORM(
        user_id=user_id,
        amount=payload.amount,
        category=payload.category,
        type=payload.type,
        note=payload.note,
        frequency=payload.frequency,
        start_date=payload.start_date,
        end_date=payload.end_date,
        next_run_date=derive_next_run_date(payload.start_date, payload.frequency, payload.end_date),
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_recurring_transaction(
    db: Session,
    *,
    item: RecurringTransactionORM,
    payload: RecurringTransactionUpdate,
) -> RecurringTransactionORM:
    today = date.today()
    (
        db.query(RecurringTransactionOccurrenceORM)
        .filter(
            RecurringTransactionOccurrenceORM.recurring_transaction_id == item.id,
            RecurringTransactionOccurrenceORM.scheduled_date >= today,
            RecurringTransactionOccurrenceORM.status != "generated",
        )
        .delete(synchronize_session=False)
    )
    item.amount = payload.amount
    item.category = payload.category
    item.type = payload.type
    item.note = payload.note
    item.frequency = payload.frequency
    item.start_date = payload.start_date
    item.end_date = payload.end_date
    item.is_active = payload.is_active
    item.next_run_date = (
        recalculate_next_run_date(db, item, today=today)
        if payload.is_active
        else None
    )
    db.commit()
    db.refresh(item)
    return item


def list_occurrences(
    db: Session,
    *,
    user_id: int,
    target_date: date | None = None,
) -> list[RecurringTransactionOccurrenceORM]:
    ensure_occurrences_for_user_month(db, user_id=user_id, target_date=target_date)
    month_start, month_end = month_bounds(target_date)
    rows = (
        db.query(RecurringTransactionOccurrenceORM)
        .options(joinedload(RecurringTransactionOccurrenceORM.recurring_transaction))
        .filter(
            RecurringTransactionOccurrenceORM.user_id == user_id,
            RecurringTransactionOccurrenceORM.scheduled_date >= month_start,
            RecurringTransactionOccurrenceORM.scheduled_date <= month_end,
        )
        .order_by(RecurringTransactionOccurrenceORM.scheduled_date.asc(), RecurringTransactionOccurrenceORM.id.asc())
        .all()
    )
    db.commit()
    return rows


def get_occurrence_or_404(db: Session, *, occurrence_id: int, user_id: int) -> RecurringTransactionOccurrenceORM:
    occurrence = (
        db.query(RecurringTransactionOccurrenceORM)
        .options(joinedload(RecurringTransactionOccurrenceORM.recurring_transaction))
        .filter(
            RecurringTransactionOccurrenceORM.id == occurrence_id,
            RecurringTransactionOccurrenceORM.user_id == user_id,
        )
        .first()
    )
    if occurrence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring occurrence not found.")
    return occurrence


def _find_existing_transaction_for_occurrence(
    db: Session,
    *,
    occurrence: RecurringTransactionOccurrenceORM,
) -> ExpenseORM | None:
    recurring = occurrence.recurring_transaction
    return (
        db.query(ExpenseORM)
        .filter(
            ExpenseORM.user_id == occurrence.user_id,
            ExpenseORM.date == occurrence.scheduled_date,
            ExpenseORM.amount == recurring.amount,
            ExpenseORM.type == recurring.type,
            ExpenseORM.category == recurring.category,
            ExpenseORM.note == recurring.note,
        )
        .first()
    )


def _build_summary(
    *,
    created_occurrence_ids: list[int] | None = None,
    skipped_occurrence_ids: list[int] | None = None,
    existing_occurrence_ids: list[int] | None = None,
    created_transaction_ids: list[int] | None = None,
) -> RecurringTransactionGenerationSummary:
    created_occurrence_ids = created_occurrence_ids or []
    skipped_occurrence_ids = skipped_occurrence_ids or []
    existing_occurrence_ids = existing_occurrence_ids or []
    created_transaction_ids = created_transaction_ids or []
    return RecurringTransactionGenerationSummary(
        created_count=len(created_occurrence_ids),
        skipped_count=len(skipped_occurrence_ids),
        already_existing_count=len(existing_occurrence_ids),
        created_transaction_ids=created_transaction_ids,
        generated_occurrence_ids=created_occurrence_ids,
        skipped_occurrence_ids=skipped_occurrence_ids,
        existing_occurrence_ids=existing_occurrence_ids,
    )


def generate_occurrence(
    db: Session,
    *,
    occurrence: RecurringTransactionOccurrenceORM,
) -> RecurringTransactionGenerationSummary:
    recurring = occurrence.recurring_transaction
    if not recurring or recurring.user_id != occurrence.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recurring occurrence is missing its schedule.")

    if occurrence.status == "skipped":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skipped occurrences cannot be generated.")

    if occurrence.status == "generated" and occurrence.generated_expense_id:
        return _build_summary(existing_occurrence_ids=[occurrence.id])

    existing_expense = _find_existing_transaction_for_occurrence(db, occurrence=occurrence)
    if existing_expense is not None:
        occurrence.status = "generated"
        occurrence.generated_expense_id = existing_expense.id
        recurring.next_run_date = recalculate_next_run_date(db, recurring)
        db.flush()
        return _build_summary(existing_occurrence_ids=[occurrence.id])

    expense = ExpenseORM(
        user_id=occurrence.user_id,
        amount=Decimal(str(recurring.amount)),
        category=recurring.category,
        type=recurring.type,
        date=occurrence.scheduled_date,
        note=recurring.note,
    )
    db.add(expense)
    db.flush()

    occurrence.status = "generated"
    occurrence.generated_expense_id = expense.id
    recurring.next_run_date = recalculate_next_run_date(db, recurring)
    db.flush()
    return _build_summary(created_occurrence_ids=[occurrence.id], created_transaction_ids=[expense.id])


def generate_current_month_transactions(
    db: Session,
    *,
    user_id: int,
    target_date: date | None = None,
) -> RecurringTransactionGenerationSummary:
    occurrences = list_occurrences(db, user_id=user_id, target_date=target_date)
    created_occurrence_ids: list[int] = []
    skipped_occurrence_ids: list[int] = []
    existing_occurrence_ids: list[int] = []
    created_transaction_ids: list[int] = []

    for occurrence in occurrences:
        if occurrence.status == "skipped":
            skipped_occurrence_ids.append(occurrence.id)
            continue
        summary = generate_occurrence(db, occurrence=occurrence)
        created_occurrence_ids.extend(summary.generated_occurrence_ids)
        skipped_occurrence_ids.extend(summary.skipped_occurrence_ids)
        existing_occurrence_ids.extend(summary.existing_occurrence_ids)
        created_transaction_ids.extend(summary.created_transaction_ids)

    db.commit()
    return _build_summary(
        created_occurrence_ids=created_occurrence_ids,
        skipped_occurrence_ids=skipped_occurrence_ids,
        existing_occurrence_ids=existing_occurrence_ids,
        created_transaction_ids=created_transaction_ids,
    )


def skip_occurrence(
    db: Session,
    *,
    occurrence: RecurringTransactionOccurrenceORM,
) -> RecurringTransactionGenerationSummary:
    if occurrence.status == "generated":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Generated occurrences cannot be skipped.")
    occurrence.status = "skipped"
    recurring = occurrence.recurring_transaction
    recurring.next_run_date = recalculate_next_run_date(db, recurring)
    db.commit()
    return _build_summary(skipped_occurrence_ids=[occurrence.id])
