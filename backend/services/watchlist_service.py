from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from db.database import SessionLocal
from models.stock import StockPriceORM, WatchlistORM
from services.stock_data_service import StockDataService

SYNC_STATUS_SUCCESS = "success"
SYNC_STATUS_PENDING = "pending"
SYNC_STATUS_FAILED = "failed"


def latest_price_for_code(db: Session, *, stock_code: str) -> StockPriceORM | None:
    return (
        db.query(StockPriceORM)
        .filter(StockPriceORM.stock_code == stock_code)
        .order_by(StockPriceORM.trade_date.desc())
        .first()
    )


def build_watchlist_item(db: Session, *, item: WatchlistORM) -> dict[str, Any]:
    latest_price = latest_price_for_code(db, stock_code=item.stock_code)
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
        "price_sync": {
            "status": sync_status,
            "provider": StockDataService.provider_name(),
            "as_of_date": latest_price.trade_date if latest_price else None,
            "last_attempt_at": item.last_sync_attempt_at,
            "error_message": item.last_sync_error,
        },
    }


def list_watchlist(db: Session, *, user_id: int) -> list[dict[str, Any]]:
    items = (
        db.query(WatchlistORM).filter(WatchlistORM.user_id == user_id).order_by(WatchlistORM.stock_code.asc()).all()
    )
    return [build_watchlist_item(db, item=item) for item in items]


def create_watchlist_item(db: Session, *, user_id: int, stock_code: str) -> WatchlistORM:
    normalized_code = StockDataService.normalize_stock_code(stock_code)
    existing = (
        db.query(WatchlistORM).filter(WatchlistORM.user_id == user_id, WatchlistORM.stock_code == normalized_code).first()
    )
    if existing:
        raise ValueError("Stock is already in the watchlist.")

    new_item = WatchlistORM(
        user_id=user_id,
        stock_code=normalized_code,
        name=None,
        price_sync_status=SYNC_STATUS_PENDING,
        last_sync_error=None,
        last_sync_attempt_at=None,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


def delete_watchlist_item(db: Session, *, user_id: int, item_id: int) -> bool:
    item = db.query(WatchlistORM).filter(WatchlistORM.id == item_id, WatchlistORM.user_id == user_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def sync_stock_price(db: Session, *, stock_code: str, watchlist_item: WatchlistORM | None = None) -> bool:
    sync_target = watchlist_item
    if sync_target is None:
        sync_target = db.query(WatchlistORM).filter(WatchlistORM.stock_code == stock_code).first()

    attempted_at = datetime.now(timezone.utc)
    try:
        price_data = StockDataService.fetch_real_price(stock_code)
    except Exception as exc:  # pragma: no cover - safety net
        price_data = None
        if sync_target:
            sync_target.price_sync_status = SYNC_STATUS_FAILED
            sync_target.last_sync_error = f"Unexpected error: {exc}"
            sync_target.last_sync_attempt_at = attempted_at
            db.commit()
        return False

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


def sync_stock_name(db: Session, *, watchlist_item: WatchlistORM) -> None:
    if watchlist_item.name:
        return
    info = StockDataService.fetch_stock_info(watchlist_item.stock_code)
    if not info:
        return
    name = info.get("shortName") or info.get("longName")
    if name:
        watchlist_item.name = str(name)[:100]
        db.commit()


def sync_watchlist_item_background(*, watchlist_item_id: int) -> None:
    db = SessionLocal()
    try:
        item = db.query(WatchlistORM).filter(WatchlistORM.id == watchlist_item_id).first()
        if not item:
            return
        sync_stock_name(db, watchlist_item=item)
        sync_stock_price(db, stock_code=item.stock_code, watchlist_item=item)
    finally:
        db.close()

