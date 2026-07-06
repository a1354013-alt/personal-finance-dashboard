from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from db.database import SessionLocal
from models.stock import StockPriceHistoryORM, StockPriceORM, WatchlistORM
from providers.stock_price import get_stock_price_provider
from providers.stock_price.base import StockQuote
from services.stock_data_service import StockDataService

SYNC_STATUS_SUCCESS = "success"
SYNC_STATUS_PENDING = "pending"
SYNC_STATUS_FAILED = "failed"
UI_STATUS_READY = "ready"
UI_STATUS_SYNC_REQUIRED = "sync_required"
UI_STATUS_ERROR = "error"


def infer_currency_for_stock_code(stock_code: str) -> str:
    return get_stock_price_provider().infer_market(stock_code)[2]


def infer_market_for_stock_code(stock_code: str) -> tuple[str, str | None, str]:
    return get_stock_price_provider().infer_market(stock_code)


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
    market, exchange, inferred_currency = infer_market_for_stock_code(item.stock_code)
    latest_close = item.last_price if item.last_price is not None else (latest_price.close if latest_price else None)
    latest_volume = item.volume if item.volume is not None else (latest_price.volume if latest_price else None)
    latest_date = latest_price.trade_date if latest_price else None
    ui_status = item.sync_status or (
        UI_STATUS_READY if latest_close is not None and sync_status == SYNC_STATUS_SUCCESS else UI_STATUS_SYNC_REQUIRED
    )
    sync_error = item.sync_error or item.last_sync_error

    return {
        "id": item.id,
        "stock_code": item.stock_code,
        "symbol": item.stock_code,
        "name": item.name or item.stock_code,
        "market": item.market or market,
        "exchange": item.exchange or exchange,
        "currency": item.currency or inferred_currency,
        "price": latest_close,
        "last_price": latest_close,
        "previous_close": item.previous_close,
        "price_change": item.price_change,
        "change_percent": item.change_percent,
        "date": latest_date,
        "volume": latest_volume,
        "provider": item.provider or StockDataService.provider_name(),
        "price_updated_at": item.price_updated_at,
        "sync_status": ui_status,
        "sync_required": bool(item.sync_required) or latest_close is None,
        "sync_error": sync_error,
        "ai_summary": item.ai_summary,
        "ai_risk_notes": item.ai_risk_notes,
        "ai_updated_at": item.ai_updated_at,
        "price_sync_status": sync_status,
        "last_sync_error": sync_error,
        "last_sync_attempt_at": item.last_sync_attempt_at,
        "price_sync": {
            "status": sync_status,
            "provider": item.provider or StockDataService.provider_name(),
            "as_of_date": latest_date,
            "last_attempt_at": item.last_sync_attempt_at,
            "error_message": sync_error,
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

    market, exchange, currency = infer_market_for_stock_code(normalized_code)
    new_item = WatchlistORM(
        user_id=user_id,
        stock_code=normalized_code,
        name=None,
        market=market,
        exchange=exchange,
        currency=currency,
        price_sync_status=SYNC_STATUS_PENDING,
        sync_status=UI_STATUS_SYNC_REQUIRED,
        sync_required=1,
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
    item.sync_status = UI_STATUS_READY if status == SYNC_STATUS_SUCCESS else UI_STATUS_ERROR if status == SYNC_STATUS_FAILED else "sync_queued"
    item.sync_required = 0 if status == SYNC_STATUS_SUCCESS else 1
    item.sync_error = error_message
    db.commit()


def quote_to_price_data(quote: StockQuote) -> dict[str, Any]:
    return {
        "stock_code": quote.stock_code,
        "trade_date": quote.trade_date,
        "open": quote.open,
        "high": quote.high,
        "low": quote.low,
        "close": quote.close,
        "volume": quote.volume,
    }


def apply_quote_to_watchlist_item(db: Session, *, watchlist_item: WatchlistORM, quote: StockQuote) -> None:
    price_change = None
    change_percent = None
    if quote.previous_close not in (None, 0):
        price_change = quote.close - quote.previous_close
        change_percent = (price_change / quote.previous_close) * 100

    watchlist_item.name = quote.name or watchlist_item.name
    watchlist_item.market = quote.market
    watchlist_item.exchange = quote.exchange
    watchlist_item.currency = quote.currency
    watchlist_item.last_price = quote.close
    watchlist_item.previous_close = quote.previous_close
    watchlist_item.price_change = price_change
    watchlist_item.change_percent = change_percent
    watchlist_item.volume = quote.volume
    watchlist_item.provider = quote.provider
    watchlist_item.price_updated_at = datetime.now(timezone.utc)
    watchlist_item.sync_status = UI_STATUS_READY
    watchlist_item.sync_required = 0
    watchlist_item.sync_error = None
    watchlist_item.price_sync_status = SYNC_STATUS_SUCCESS
    watchlist_item.last_sync_error = None
    watchlist_item.last_sync_attempt_at = watchlist_item.price_updated_at
    db.commit()


def sync_watchlist_item_now(db: Session, *, watchlist_item: WatchlistORM) -> bool:
    attempted_at = datetime.now(timezone.utc)
    provider = get_stock_price_provider()
    quote = provider.fetch_quote(watchlist_item.stock_code)
    if not quote:
        watchlist_item.price_sync_status = SYNC_STATUS_FAILED
        watchlist_item.last_sync_error = "Unable to fetch latest price data from the upstream provider."
        watchlist_item.last_sync_attempt_at = attempted_at
        watchlist_item.sync_status = UI_STATUS_ERROR
        watchlist_item.sync_required = 1
        watchlist_item.sync_error = watchlist_item.last_sync_error
        watchlist_item.provider = provider.name
        db.commit()
        return False

    upsert_stock_price_history(db, price_data=quote_to_price_data(quote), source=quote.provider, commit=False)
    apply_quote_to_watchlist_item(db, watchlist_item=watchlist_item, quote=quote)
    return True


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
    quote = None
    try:
        quote = get_stock_price_provider().fetch_quote(stock_code)
        price_data = quote_to_price_data(quote) if quote else None
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

    upsert_stock_price_history(
        db,
        price_data=price_data,
        source=quote.provider if quote else StockDataService.provider_name(),
        commit=False,
    )
    if quote:
        apply_quote_to_watchlist_item(db, watchlist_item=sync_target, quote=quote)
        return True

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

