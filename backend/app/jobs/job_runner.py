from __future__ import annotations

import json
import logging
import queue
import threading
import time
from datetime import date, datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from db.database import SessionLocal
from logging_config import bind_request_id
from models.fundamentals import FundamentalsORM
from models.job import (
    JOB_STATUS_FAILED,
    JOB_STATUS_PENDING,
    JOB_STATUS_RETRYING,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCESS,
    SyncJobORM,
)
from providers.fundamentals import get_fundamentals_provider
from providers.fundamentals.base import FundamentalsProviderError
from services.stock_data_service import StockDataService
from services.watchlist_service import update_watchlist_sync_status, upsert_stock_price_history

logger = logging.getLogger(__name__)

JOB_TYPE_SYNC_FUNDAMENTALS = "sync_fundamentals"
JOB_TYPE_SYNC_STOCK_MARKET_DATA = "sync_stock_market_data"


class JobRunner:
    def __init__(self) -> None:
        self._queue: queue.Queue[int] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._handlers: dict[str, Callable[[Session, SyncJobORM, dict], None]] = {
            JOB_TYPE_SYNC_FUNDAMENTALS: self._handle_fundamentals_sync,
            JOB_TYPE_SYNC_STOCK_MARKET_DATA: self._handle_stock_market_data_sync,
        }

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="job-runner", daemon=True)
        self._thread.start()
        self.enqueue_pending_jobs()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def enqueue(self, job_id: int) -> None:
        self._queue.put(job_id)

    def enqueue_pending_jobs(self) -> None:
        with SessionLocal() as db:
            jobs = (
                db.query(SyncJobORM)
                .filter(SyncJobORM.status.in_([JOB_STATUS_PENDING, JOB_STATUS_RETRYING, JOB_STATUS_RUNNING]))
                .order_by(SyncJobORM.created_at.asc())
                .all()
            )
            for job in jobs:
                self.enqueue(job.id)

    def drain_once(self) -> bool:
        try:
            job_id = self._queue.get_nowait()
        except queue.Empty:
            return False
        self._process_job_id(job_id)
        return True

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                job_id = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self._process_job_id(job_id)

    def _process_job_id(self, job_id: int) -> None:
        with SessionLocal() as db:
            job = db.query(SyncJobORM).filter(SyncJobORM.id == job_id).first()
            if not job or job.status == JOB_STATUS_SUCCESS:
                return

            payload = json.loads(job.payload)
            bind_request_id(job.request_id)
            job.attempts += 1
            job.status = JOB_STATUS_RUNNING
            job.started_at = datetime.now(timezone.utc)
            job.updated_at = job.started_at
            db.commit()

            try:
                handler = self._handlers[job.job_type]
                handler(db, job, payload)
                job.status = JOB_STATUS_SUCCESS
                job.error_message = None
                job.completed_at = datetime.now(timezone.utc)
                job.updated_at = job.completed_at
                db.commit()
                logger.info(
                    "job completed",
                    extra={"job_id": job.id, "job_type": job.job_type, "attempt": job.attempts},
                )
            except Exception as exc:  # pragma: no cover - exercised via tests with controlled failures
                db.rollback()
                job = db.query(SyncJobORM).filter(SyncJobORM.id == job_id).first()
                if job is None:
                    return
                job.error_message = str(exc)
                job.updated_at = datetime.now(timezone.utc)
                if job.attempts < job.max_attempts:
                    job.status = JOB_STATUS_RETRYING
                    db.commit()
                    logger.warning(
                        "job retry scheduled",
                        extra={"job_id": job.id, "job_type": job.job_type, "attempt": job.attempts},
                        exc_info=exc,
                    )
                    time.sleep(0.05)
                    self.enqueue(job.id)
                else:
                    job.status = JOB_STATUS_FAILED
                    job.completed_at = datetime.now(timezone.utc)
                    db.commit()
                    logger.error(
                        "job failed",
                        extra={"job_id": job.id, "job_type": job.job_type, "attempt": job.attempts},
                        exc_info=exc,
                    )

    def _handle_fundamentals_sync(self, db: Session, job: SyncJobORM, payload: dict) -> None:
        stock_code = str(payload["stock_code"]).upper()
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
            row = FundamentalsORM(stock_code=stock_code, source=provider.name, as_of_date=date.today())
            db.add(row)
            db.flush()

        try:
            result = provider.fetch(stock_code=stock_code)
        except FundamentalsProviderError as exc:
            row.status = JOB_STATUS_FAILED
            row.error_message = str(exc)
            row.fetched_at = datetime.now(timezone.utc)
            db.commit()
            raise
        except Exception as exc:
            row.status = JOB_STATUS_FAILED
            row.error_message = f"Unexpected error: {exc}"
            row.fetched_at = datetime.now(timezone.utc)
            db.commit()
            raise

        row.pe_ratio = result.pe_ratio
        row.pb_ratio = result.pb_ratio
        row.dividend_yield = result.dividend_yield
        row.revenue_growth = result.revenue_growth
        row.eps = result.eps
        row.status = JOB_STATUS_SUCCESS
        row.error_message = None
        row.fetched_at = datetime.now(timezone.utc)
        db.commit()

    def _handle_stock_market_data_sync(self, db: Session, job: SyncJobORM, payload: dict) -> None:
        stock_code = StockDataService.normalize_stock_code(str(payload["stock_code"]))
        user_id = int(payload["user_id"])
        watchlist_item_id = int(payload["watchlist_item_id"])
        from models.stock import WatchlistORM

        watchlist_item = (
            db.query(WatchlistORM)
            .filter(
                WatchlistORM.id == watchlist_item_id,
                WatchlistORM.user_id == user_id,
                WatchlistORM.stock_code == stock_code,
            )
            .first()
        )
        if not watchlist_item:
            raise RuntimeError("watchlist item no longer exists")

        history = StockDataService.fetch_price_history(stock_code)
        info = StockDataService.fetch_stock_info(stock_code)
        if not history:
            update_watchlist_sync_status(
                db,
                watchlist_item_id=watchlist_item_id,
                user_id=user_id,
                status=JOB_STATUS_FAILED,
                error_message="Unable to fetch latest price data from the upstream provider.",
            )
            raise RuntimeError(f"price sync failed for {stock_code}")

        for point in history:
            upsert_stock_price_history(
                db,
                price_data=point,
                source=StockDataService.provider_name(),
                commit=False,
            )
        db.commit()
        update_watchlist_sync_status(
            db,
            watchlist_item_id=watchlist_item_id,
            user_id=user_id,
            status=JOB_STATUS_SUCCESS,
            error_message=None,
        )

        display_name = (info or {}).get("shortName") or (info or {}).get("longName")
        if display_name:
            watchlist_item.name = str(display_name)[:100]
            db.commit()


_job_runner = JobRunner()


def get_job_runner() -> JobRunner:
    return _job_runner
