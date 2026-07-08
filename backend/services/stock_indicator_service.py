from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy.orm import Session

from models.stock import StockPriceHistoryORM, WatchlistORM

DISCLAIMER = "This is informational only and not financial advice."


def _round_indicator(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _average(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal("0")) / Decimal(len(values))


def calculate_rsi14(closes: list[Decimal]) -> Decimal | None:
    if len(closes) < 15:
        return None

    recent = closes[-15:]
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for previous, current in zip(recent, recent[1:]):
        change = current - previous
        if change > 0:
            gains.append(change)
            losses.append(Decimal("0"))
        else:
            gains.append(Decimal("0"))
            losses.append(abs(change))

    average_gain = _average(gains)
    average_loss = _average(losses)

    if average_loss == 0:
        return Decimal("100.00") if average_gain > 0 else Decimal("50.00")
    if average_gain == 0:
        return Decimal("0.00")

    relative_strength = average_gain / average_loss
    rsi = Decimal("100") - (Decimal("100") / (Decimal("1") + relative_strength))
    return _round_indicator(rsi)


def build_stock_indicators(db: Session, *, watchlist_item: WatchlistORM) -> dict[str, Any]:
    rows = (
        db.query(StockPriceHistoryORM)
        .filter(StockPriceHistoryORM.stock_code == watchlist_item.stock_code)
        .order_by(StockPriceHistoryORM.trade_date.asc())
        .all()
    )
    if not rows:
        return {
            "watchlist_item_id": watchlist_item.id,
            "symbol": watchlist_item.stock_code,
            "as_of_date": None,
            "latest_close": None,
            "ma5": None,
            "ma20": None,
            "rsi14": None,
            "status": "no_price_history",
            "disclaimer": DISCLAIMER,
        }

    closes = [Decimal(row.close) for row in rows]
    latest = rows[-1]
    enough_history = len(closes) >= 20
    return {
        "watchlist_item_id": watchlist_item.id,
        "symbol": watchlist_item.stock_code,
        "as_of_date": latest.trade_date,
        "latest_close": latest.close,
        "ma5": _round_indicator(_average(closes[-5:])) if len(closes) >= 5 else None,
        "ma20": _round_indicator(_average(closes[-20:])) if len(closes) >= 20 else None,
        "rsi14": calculate_rsi14(closes),
        "status": "ready" if enough_history else "insufficient_history",
        "disclaimer": DISCLAIMER,
    }
