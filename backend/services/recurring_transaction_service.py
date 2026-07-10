from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

from sqlalchemy.orm import Session

from models.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionORM,
    RecurringTransactionUpdate,
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
    if not recurring.is_active or not recurring.next_run_date:
        return []
    today = today or date.today()
    current = recurring.next_run_date
    if current < today:
        current = derive_next_run_date(recurring.start_date, recurring.frequency, recurring.end_date, today=today)
    dates: list[date] = []
    while current and current <= end_date:
        if recurring.end_date and current > recurring.end_date:
            break
        if current >= today:
            dates.append(current)
        current = advance_date(current, recurring.frequency)
    return dates


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
    item.amount = payload.amount
    item.category = payload.category
    item.type = payload.type
    item.note = payload.note
    item.frequency = payload.frequency
    item.start_date = payload.start_date
    item.end_date = payload.end_date
    item.is_active = payload.is_active
    item.next_run_date = (
        derive_next_run_date(payload.start_date, payload.frequency, payload.end_date)
        if payload.is_active
        else None
    )
    db.commit()
    db.refresh(item)
    return item
