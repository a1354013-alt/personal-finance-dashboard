from __future__ import annotations

import os

from sqlalchemy.orm import Session

from models.fundamentals import FundamentalsSnapshot
from models.stock import WatchlistORM
from models.stocks_filter import FilterMetadataResponse, FundamentalsStatusMeta, StockFundamentalsFilterResult
from providers.fundamentals import get_fundamentals_provider
from services.fundamentals_screening import screen_fundamentals
from services.fundamentals_service import fundamentals_ttl_hours, get_latest_fundamentals_by_code, is_stale


def build_filter_results(*, db: Session, user_id: int) -> list[StockFundamentalsFilterResult]:
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == user_id).all()
    codes = {item.stock_code for item in watchlist}
    latest = get_latest_fundamentals_by_code(db, codes)

    results: list[StockFundamentalsFilterResult] = []
    ttl = fundamentals_ttl_hours()
    provider_name = get_fundamentals_provider().name

    for code in sorted(codes):
        row = latest.get(code)
        if row is None:
            results.append(
                StockFundamentalsFilterResult(
                    stock_code=code,
                    passed=False,
                    fail_reasons=["No fundamentals cached yet. Sync required."],
                    fundamentals=None,
                    meta=FundamentalsStatusMeta(
                        provider=provider_name,
                        ttl_hours=ttl,
                        is_stale=True,
                        fetched_at=None,
                        as_of_date=None,
                        status=None,
                        error_message=None,
                    ),
                )
            )
            continue

        screen = screen_fundamentals(row)
        results.append(
            StockFundamentalsFilterResult(
                stock_code=code,
                passed=screen.passed,
                fail_reasons=screen.fail_reasons,
                fundamentals=FundamentalsSnapshot.model_validate(row),
                meta=FundamentalsStatusMeta(
                    provider=row.source,
                    ttl_hours=ttl,
                    is_stale=is_stale(fetched_at=row.fetched_at, ttl_hours=ttl),
                    fetched_at=row.fetched_at,
                    as_of_date=row.as_of_date.isoformat(),
                    status=row.status,
                    error_message=row.error_message,
                ),
            )
        )
    return results


def build_filter_metadata() -> FilterMetadataResponse:
    provider = get_fundamentals_provider()
    ttl = fundamentals_ttl_hours()
    timeout = float(os.getenv("FUNDAMENTALS_TIMEOUT_SECONDS", "8"))
    return FilterMetadataResponse(
        fundamentals_provider=provider.name,
        ttl_hours=ttl,
        timeout_seconds=timeout,
        message=(
            "Fundamentals screening reads cached data from the database. "
            "Sync fundamentals explicitly to refresh; screening does not fetch live data per request."
        ),
    )

