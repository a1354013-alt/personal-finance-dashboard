from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from models.fundamentals import FundamentalsORM
from providers.fundamentals.base import BaseFundamentalsProvider, FundamentalsProviderError

STATUS_PENDING = "pending"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"


def fundamentals_ttl_hours() -> int:
    raw = os.getenv("FUNDAMENTALS_TTL_HOURS", "24")
    try:
        ttl = int(raw)
        return max(1, ttl)
    except ValueError:
        return 24


def is_stale(*, fetched_at: datetime | None, ttl_hours: int | None = None) -> bool:
    if fetched_at is None:
        return True
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    ttl = ttl_hours if ttl_hours is not None else fundamentals_ttl_hours()
    return fetched_at < (datetime.now(timezone.utc) - timedelta(hours=ttl))


def get_latest_fundamentals_by_code(db: Session, stock_codes: set[str]) -> dict[str, FundamentalsORM]:
    if not stock_codes:
        return {}

    rows = (
        db.query(FundamentalsORM)
        .filter(FundamentalsORM.stock_code.in_(sorted(stock_codes)))
        .order_by(FundamentalsORM.stock_code.asc(), FundamentalsORM.as_of_date.desc(), FundamentalsORM.fetched_at.desc())
        .all()
    )

    latest: dict[str, FundamentalsORM] = {}
    for row in rows:
        if row.stock_code not in latest:
            latest[row.stock_code] = row
    return latest


def sync_fundamentals(
    db: Session,
    *,
    stock_code: str,
    provider: BaseFundamentalsProvider,
    force: bool = False,
) -> FundamentalsORM:
    now = datetime.now(timezone.utc)
    as_of = date.today()
    source = provider.name

    row = (
        db.query(FundamentalsORM)
        .filter(
            FundamentalsORM.stock_code == stock_code,
            FundamentalsORM.source == source,
            FundamentalsORM.as_of_date == as_of,
        )
        .first()
    )

    if row and not force and row.status == STATUS_SUCCESS and not is_stale(fetched_at=row.fetched_at):
        return row

    if not row:
        row = FundamentalsORM(stock_code=stock_code, source=source, as_of_date=as_of, status=STATUS_PENDING)
        db.add(row)
        db.flush()

    try:
        result = provider.fetch(stock_code=stock_code)
        row.pe_ratio = result.pe_ratio
        row.pb_ratio = result.pb_ratio
        row.dividend_yield = result.dividend_yield
        row.revenue_growth = result.revenue_growth
        row.eps = result.eps
        row.status = STATUS_SUCCESS
        row.error_message = None
    except FundamentalsProviderError as exc:
        row.status = STATUS_FAILED
        row.error_message = str(exc)
    except Exception as exc:
        row.status = STATUS_FAILED
        row.error_message = f"Unexpected error: {exc}"

    row.fetched_at = now
    db.commit()
    db.refresh(row)
    return row
