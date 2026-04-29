from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.jobs.job_runner import JOB_TYPE_SYNC_FUNDAMENTALS
from models.fundamentals import FundamentalsORM
from models.job import CreateJobRequest
from providers.fundamentals import get_fundamentals_provider
from services.job_service import create_job

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


def queue_fundamentals_sync(
    db: Session,
    *,
    stock_code: str,
    request_id: str | None,
    force: bool = False,
) -> FundamentalsORM:
    provider = get_fundamentals_provider()
    row = (
        db.query(FundamentalsORM)
        .filter(
            FundamentalsORM.stock_code == stock_code,
            FundamentalsORM.source == provider.name,
            FundamentalsORM.as_of_date == date.today(),
        )
        .first()
    )

    if row is None:
        row = FundamentalsORM(
            stock_code=stock_code,
            source=provider.name,
            as_of_date=date.today(),
            status=STATUS_PENDING,
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(row)
    else:
        row.status = STATUS_PENDING
        row.error_message = None
        if force:
            row.fetched_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)

    create_job(
        db,
        CreateJobRequest(
            job_type=JOB_TYPE_SYNC_FUNDAMENTALS,
            payload={"stock_code": stock_code, "force": force},
            request_id=request_id,
            max_attempts=3,
        ),
    )
    db.refresh(row)
    return row
