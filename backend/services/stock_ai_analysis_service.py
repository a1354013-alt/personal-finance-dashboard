from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from models.ai import AIProviderMeta
from models.stock import StockAIAnalysisResponse, WatchlistORM
from providers.llm import get_llm_provider
from services.ai_service import AIInsightsService

DISCLAIMER = "This is informational only and not financial advice."
_BANNED_TERMS = {
    "buy": "consider",
    "sell": "review",
    "must buy": "requires review",
    "guaranteed": "uncertain",
    "target price": "price level",
}


def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _sanitize_text(value: str) -> str:
    text = value or ""
    for banned, replacement in _BANNED_TERMS.items():
        text = text.replace(banned, replacement).replace(banned.title(), replacement.title())
    if DISCLAIMER not in text:
        text = f"{text.rstrip()}\n{DISCLAIMER}" if text.strip() else DISCLAIMER
    return text


def _movement_note(item: WatchlistORM) -> str:
    if item.price_change is None or item.change_percent is None:
        return "Recent price movement is unavailable until price data includes a previous close."
    change = _to_float(item.price_change)
    percent = _to_float(item.change_percent)
    direction = "higher" if change and change > 0 else "lower" if change and change < 0 else "flat"
    return f"The latest cached price is {direction} by {change:.2f} {item.currency or ''} ({percent:.2f}%)."


def _volume_note(item: WatchlistORM) -> str:
    if item.volume is None:
        return "Volume data is unavailable from the latest cached provider response."
    return f"Latest cached volume is {item.volume:,} shares; compare it with typical volume before drawing conclusions."


def build_stock_ai_analysis(
    db: Session,
    *,
    watchlist_item: WatchlistORM,
) -> StockAIAnalysisResponse:
    if watchlist_item.last_price is None:
        return StockAIAnalysisResponse(
            status="sync_required",
            stock_code=watchlist_item.stock_code,
            summary="Price data is unavailable. Sync this watchlist item before requesting interpretation.",
            recent_price_movement=None,
            volume_note=None,
            risk_notes=["Cached market data is missing or stale."],
            watch_points=["Run price sync and confirm the as-of time."],
            disclaimer=DISCLAIMER,
        )

    payload = {
        "stock_code": watchlist_item.stock_code,
        "name": watchlist_item.name,
        "market": watchlist_item.market,
        "exchange": watchlist_item.exchange,
        "currency": watchlist_item.currency,
        "last_price": _to_float(watchlist_item.last_price),
        "previous_close": _to_float(watchlist_item.previous_close),
        "price_change": _to_float(watchlist_item.price_change),
        "change_percent": _to_float(watchlist_item.change_percent),
        "volume": watchlist_item.volume,
        "provider": watchlist_item.provider,
        "price_updated_at": watchlist_item.price_updated_at,
    }
    result = AIInsightsService(get_llm_provider()).stock_interpretation(stock_payload=payload)
    summary = _sanitize_text(result.text)
    risk_notes = [
        "Single-symbol concentration can increase volatility.",
        "Provider data may be delayed, incomplete, or unavailable during market holidays.",
    ]
    watch_points = [
        "Check whether the latest price timestamp is current.",
        "Compare volume changes with recent average activity.",
        "Review fundamentals and news outside this cached dashboard data.",
    ]
    watchlist_item.ai_summary = summary
    watchlist_item.ai_risk_notes = "\n".join(risk_notes)
    watchlist_item.ai_updated_at = datetime.now(timezone.utc)
    db.commit()

    return StockAIAnalysisResponse(
        status="ready",
        stock_code=watchlist_item.stock_code,
        summary=summary,
        recent_price_movement=_movement_note(watchlist_item),
        volume_note=_volume_note(watchlist_item),
        risk_notes=risk_notes,
        watch_points=watch_points,
        disclaimer=DISCLAIMER,
        meta=AIProviderMeta(provider=result.provider, is_fallback=result.is_fallback, error=result.error),
    )
