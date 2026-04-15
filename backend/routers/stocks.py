from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.fundamentals import FundamentalsSnapshot, FundamentalsSyncOptions
from models.stock import (
    StockFilterRequest,
    StockFilterResult,
    StockPriceORM,
    WatchlistCreate,
    WatchlistItemResponse,
    WatchlistORM,
)
from models.stocks_filter import FilterMetadataResponse, FundamentalsStatusMeta, StockFundamentalsFilterResult
from models.user import UserORM
from providers.fundamentals import get_fundamentals_provider
from services.auth import get_current_user
from services.fundamentals_screening import screen_fundamentals
from services.fundamentals_service import fundamentals_ttl_hours, get_latest_fundamentals_by_code, is_stale, sync_fundamentals
from services.stock_data_service import StockDataService
from services.stock_filter import evaluate_stock

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])

SYNC_STATUS_SUCCESS = "success"
SYNC_STATUS_PENDING = "pending"
SYNC_STATUS_FAILED = "failed"


def _latest_price_for_code(db: Session, stock_code: str) -> StockPriceORM | None:
    return (
        db.query(StockPriceORM)
        .filter(StockPriceORM.stock_code == stock_code)
        .order_by(StockPriceORM.trade_date.desc())
        .first()
    )


def _build_watchlist_item(db: Session, item: WatchlistORM) -> dict:
    latest_price = _latest_price_for_code(db, item.stock_code)
    # Sync status semantics are persistence-first:
    # - pending: sync has not succeeded yet
    # - success: latest sync succeeded
    # - failed: latest sync attempt failed
    # Price rows are display data only and must not overwrite persisted sync status.
    sync_status = item.price_sync_status or SYNC_STATUS_PENDING

    return {
        "id": item.id,
        "user_id": item.user_id,
        "stock_code": item.stock_code,
        "name": item.name or item.stock_code,
        "price": latest_price.close if latest_price else None,
        "date": latest_price.trade_date if latest_price else None,
        "volume": latest_price.volume if latest_price else None,
        "price_sync_status": sync_status,
        "last_sync_error": item.last_sync_error,
        "last_sync_attempt_at": item.last_sync_attempt_at,
    }


@router.get("/watchlist", response_model=list[WatchlistItemResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    items = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.user_id == current_user.id)
        .order_by(WatchlistORM.stock_code.asc())
        .all()
    )
    return [_build_watchlist_item(db, item) for item in items]


@router.post("/watchlist", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    request: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    stock_code = StockDataService._format_stock_code(request.stock_code)

    existing = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.user_id == current_user.id, WatchlistORM.stock_code == stock_code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock is already in the watchlist.")

    stock_info = StockDataService.fetch_stock_info(stock_code)
    stock_name = stock_info.get("shortName") or stock_info.get("longName") if stock_info else None

    new_item = WatchlistORM(
        user_id=current_user.id,
        stock_code=stock_code,
        name=stock_name,
        price_sync_status=SYNC_STATUS_PENDING,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    _sync_stock_price_internal(stock_code, db, new_item)
    db.refresh(new_item)
    return _build_watchlist_item(db, new_item)


@router.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_from_watchlist(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    item = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.id == item_id, WatchlistORM.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")

    db.delete(item)
    db.commit()


@router.post("/fundamentals/sync", response_model=list[FundamentalsSnapshot])
def sync_watchlist_fundamentals(
    payload: FundamentalsSyncOptions,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    # IMPORTANT: this route must be defined before `/{stock_code}/sync` to avoid path conflicts.
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    provider = get_fundamentals_provider()
    rows = [
        sync_fundamentals(db, stock_code=item.stock_code, provider=provider, force=payload.force) for item in watchlist
    ]
    return [FundamentalsSnapshot.model_validate(row) for row in rows]


@router.post("/fundamentals/{stock_code}/sync", response_model=FundamentalsSnapshot)
def sync_single_fundamentals(
    stock_code: str,
    payload: FundamentalsSyncOptions,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    formatted_code = StockDataService._format_stock_code(stock_code)
    watchlist_item = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.user_id == current_user.id, WatchlistORM.stock_code == formatted_code)
        .first()
    )
    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Stock is not in your watchlist.")

    provider = get_fundamentals_provider()
    row = sync_fundamentals(db, stock_code=formatted_code, provider=provider, force=payload.force)
    return FundamentalsSnapshot.model_validate(row)


@router.get("/fundamentals", response_model=list[FundamentalsSnapshot])
def get_watchlist_fundamentals(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    codes = {item.stock_code for item in watchlist}
    latest = get_latest_fundamentals_by_code(db, codes)
    return [FundamentalsSnapshot.model_validate(latest[code]) for code in sorted(latest)]


@router.post("/sync")
def sync_all_watchlist_prices(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    success_count = 0
    failed_codes: list[str] = []

    for item in watchlist:
        if _sync_stock_price_internal(item.stock_code, db, item):
            success_count += 1
        else:
            failed_codes.append(item.stock_code)

    return {
        "message": f"Synchronized {success_count} of {len(watchlist)} watchlist items.",
        "success_count": success_count,
        "failed_codes": failed_codes,
    }


@router.post("/{stock_code}/sync")
def sync_single_stock_price(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    formatted_code = StockDataService._format_stock_code(stock_code)
    watchlist_item = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.user_id == current_user.id, WatchlistORM.stock_code == formatted_code)
        .first()
    )
    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Stock is not in your watchlist.")

    if _sync_stock_price_internal(formatted_code, db, watchlist_item):
        return {"message": f"Synchronized {formatted_code} successfully.", "price_sync_status": SYNC_STATUS_SUCCESS}

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Unable to fetch the latest price for {formatted_code}.",
    )


def _sync_stock_price_internal(stock_code: str, db: Session, watchlist_item: WatchlistORM | None = None) -> bool:
    sync_target = watchlist_item
    if sync_target is None:
        sync_target = db.query(WatchlistORM).filter(WatchlistORM.stock_code == stock_code).first()

    price_data = StockDataService.fetch_real_price(stock_code)
    attempted_at = datetime.now(timezone.utc)

    if not price_data:
        if sync_target:
            sync_target.price_sync_status = SYNC_STATUS_FAILED
            sync_target.last_sync_error = "Unable to fetch latest price data from the upstream provider."
            sync_target.last_sync_attempt_at = attempted_at
            db.commit()
        return False

    existing = (
        db.query(StockPriceORM)
        .filter(
            StockPriceORM.stock_code == price_data["stock_code"],
            StockPriceORM.trade_date == price_data["trade_date"],
        )
        .first()
    )

    if existing:
        existing.open = price_data["open"]
        existing.high = price_data["high"]
        existing.low = price_data["low"]
        existing.close = price_data["close"]
        existing.volume = price_data["volume"]
    else:
        db.add(StockPriceORM(**price_data))

    if sync_target:
        sync_target.price_sync_status = SYNC_STATUS_SUCCESS
        sync_target.last_sync_error = None
        sync_target.last_sync_attempt_at = attempted_at

    db.commit()
    return True


@router.get("/filter", response_model=list[StockFundamentalsFilterResult])
def filter_watchlist_stocks(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
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


@router.get("/filter-metadata", response_model=FilterMetadataResponse)
def get_filter_metadata():
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




@router.post("/filter", response_model=StockFilterResult)
def filter_single_stock(payload: StockFilterRequest):
    return evaluate_stock(
        stock_code=payload.stock_code,
        net_income=payload.net_income,
        free_cash_flow=payload.free_cash_flow,
        revenue_growth=payload.revenue_growth,
    )
