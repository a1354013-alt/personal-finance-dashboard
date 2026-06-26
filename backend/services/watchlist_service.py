from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from db.database import SessionLocal
from models.stock import StockPriceHistoryORM, StockPriceORM, WatchlistORM
from services.stock_data_service import StockDataService

SYNC_STATUS_SUCCESS = "success"
SYNC_STATUS_PENDING = "pending"
SYNC_STATUS_FAILED = "failed"


def infer_currency_for_stock_code(stock_code: str) -> str:
    normalized_code = StockDataService.normalize_stock_code(stock_code)
    if normalized_code.endswith(".TW") or normalized_code.endswith(".TWO"):
        return "TWD"
    return "USD"


def latest_price_for_code(db: Session, *, stock_code: str) -> StockPriceORM | None:
    return (
        db.query(StockPriceORM)
        .filter(StockPriceORM.stock_code == stock_code)
        .order_by(StockPriceORM.trade_date.desc())
        .first()
    )


def latest_history_for_code(db: Session, *, stock_code: str) -> StockPriceHistoryORM | None:
    return (
        db.query(StockPriceHistoryORM)
        .filter(StockPriceHistoryORM.stock_code == stock_code)
        .order_by(StockPriceHistoryORM.trade_date.desc())
        .first()
    )


def build_watchlist_item(db: Session, *, item: WatchlistORM) -> dict[str, Any]:
    latest_price = latest_history_for_code(db, stock_code=item.stock_code) or latest_price_for_code(
        db, stock_code=item.stock_code
    )
    sync_status = item.price_sync_status or SYNC_STATUS_PENDING

    return {
        "id": item.id,
        "stock_code": item.stock_code,
        "name": item.name or item.stock_code,
        "price": latest_price.close if latest_price else None,
        "currency": infer_currency_for_stock_code(item.stock_code),
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


def update_watchlist_sync_status(
    db: Session,
    *,
    watchlist_item_id: int,
    user_id: int,
    status: str,
    error_message: str | None,
) -> None:
    attempted_at = datetime.now(timezone.utc)
    item = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.id == watchlist_item_id, WatchlistORM.user_id == user_id)
        .first()
    )
    if not item:
        return
    item.price_sync_status = status
    item.last_sync_error = error_message
    item.last_sync_attempt_at = attempted_at
    db.commit()


def upsert_stock_price_history(
    db: Session,
    *,
    price_data: dict[str, Any],
    source: str,
    commit: bool = True,
) -> None:
    existing_history = (
        db.query(StockPriceHistoryORM)
        .filter(
            StockPriceHistoryORM.stock_code == price_data["stock_code"],
            StockPriceHistoryORM.trade_date == price_data["trade_date"],
        )
        .first()
    )
    if existing_history:
        existing_history.open = price_data["open"]
        existing_history.high = price_data["high"]
        existing_history.low = price_data["low"]
        existing_history.close = price_data["close"]
        existing_history.volume = price_data["volume"]
        existing_history.source = source
    else:
        db.add(StockPriceHistoryORM(source=source, **price_data))

    existing_latest = (
        db.query(StockPriceORM)
        .filter(
            StockPriceORM.stock_code == price_data["stock_code"],
            StockPriceORM.trade_date == price_data["trade_date"],
        )
        .first()
    )
    if existing_latest:
        existing_latest.open = price_data["open"]
        existing_latest.high = price_data["high"]
        existing_latest.low = price_data["low"]
        existing_latest.close = price_data["close"]
        existing_latest.volume = price_data["volume"]
    else:
        db.add(StockPriceORM(**price_data))
    if commit:
        db.commit()


def sync_stock_price(db: Session, *, stock_code: str, watchlist_item: WatchlistORM) -> bool:
    # Safety: require a user-scoped watchlist item to avoid cross-user updates.
    sync_target = watchlist_item
    stock_code = sync_target.stock_code

    attempted_at = datetime.now(timezone.utc)
    try:
        price_data = StockDataService.fetch_real_price(stock_code)
    except Exception as exc:  # pragma: no cover - safety net
        price_data = None
        sync_target.price_sync_status = SYNC_STATUS_FAILED
        sync_target.last_sync_error = f"Unexpected error: {exc}"
        sync_target.last_sync_attempt_at = attempted_at
        db.commit()
        return False

    if not price_data:
        sync_target.price_sync_status = SYNC_STATUS_FAILED
        sync_target.last_sync_error = "Unable to fetch latest price data from the upstream provider."
        sync_target.last_sync_attempt_at = attempted_at
        db.commit()
        return False

    upsert_stock_price_history(db, price_data=price_data, source=StockDataService.provider_name(), commit=False)

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

