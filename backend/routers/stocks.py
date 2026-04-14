from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.stock import (
    StockFilterRequest,
    StockFilterResult,
    StockPriceORM,
    WatchlistCreate,
    WatchlistItemResponse,
    WatchlistORM,
)
from models.user import UserORM
from services.auth import get_current_user
from services.stock_data_service import StockDataService
from services.stock_filter import evaluate_stock

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])

SYNC_STATUS_SUCCESS = "success"
SYNC_STATUS_PENDING = "pending"
SYNC_STATUS_FAILED = "failed"

MOCK_FUNDAMENTALS = [
    {"stock_code": "2330.TW", "net_income": 500_000, "free_cash_flow": 300_000, "revenue_growth": 12.5},
    {"stock_code": "2317.TW", "net_income": 80_000, "free_cash_flow": -5_000, "revenue_growth": 3.2},
    {"stock_code": "2454.TW", "net_income": 120_000, "free_cash_flow": 90_000, "revenue_growth": -2.1},
    {"stock_code": "2382.TW", "net_income": 45_000, "free_cash_flow": 30_000, "revenue_growth": 8.7},
    {"stock_code": "AAPL", "net_income": 970_000, "free_cash_flow": 850_000, "revenue_growth": 5.0},
    {"stock_code": "NVDA", "net_income": 430_000, "free_cash_flow": 380_000, "revenue_growth": 122.0},
]
MOCK_FUNDAMENTAL_CODES = {item["stock_code"] for item in MOCK_FUNDAMENTALS}


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


@router.get("/filter", response_model=list[StockFilterResult])
def filter_watchlist_stocks(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    watchlist_codes = {stock.stock_code for stock in watchlist}

    results = []
    for stock in MOCK_FUNDAMENTALS:
        if stock["stock_code"] in watchlist_codes:
            results.append(
                evaluate_stock(
                    stock_code=stock["stock_code"],
                    net_income=stock["net_income"],
                    free_cash_flow=stock["free_cash_flow"],
                    revenue_growth=stock["revenue_growth"],
                )
            )
    return results


@router.get("/filter-metadata")
def get_filter_metadata():
    return {
        "mock_only": True,
        "supported_codes": sorted(MOCK_FUNDAMENTAL_CODES),
        "message": "Screening results are available only for the bundled mock fundamentals list.",
    }


@router.post("/filter", response_model=StockFilterResult)
def filter_single_stock(payload: StockFilterRequest):
    return evaluate_stock(
        stock_code=payload.stock_code,
        net_income=payload.net_income,
        free_cash_flow=payload.free_cash_flow,
        revenue_growth=payload.revenue_growth,
    )
