from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from models.stock import StockPriceAlertORM, StockPriceAlertUpdate, WatchlistORM


def list_stock_alerts(db: Session, *, user_id: int) -> list[StockPriceAlertORM]:
    return (
        db.query(StockPriceAlertORM)
        .filter(StockPriceAlertORM.user_id == user_id)
        .order_by(StockPriceAlertORM.created_at.desc(), StockPriceAlertORM.id.desc())
        .all()
    )


def create_stock_alert(
    db: Session,
    *,
    user_id: int,
    watchlist_item: WatchlistORM,
    condition_type: str,
    target_price: Decimal,
) -> StockPriceAlertORM:
    now = datetime.now(timezone.utc)
    alert = StockPriceAlertORM(
        user_id=user_id,
        watchlist_item_id=watchlist_item.id,
        symbol=watchlist_item.stock_code,
        condition_type=condition_type,
        target_price=target_price,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def update_stock_alert(
    db: Session,
    *,
    user_id: int,
    alert_id: int,
    payload: StockPriceAlertUpdate,
) -> StockPriceAlertORM | None:
    alert = db.query(StockPriceAlertORM).filter(StockPriceAlertORM.id == alert_id, StockPriceAlertORM.user_id == user_id).first()
    if not alert:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if "condition_type" in update_data:
        alert.condition_type = update_data["condition_type"]
    if "target_price" in update_data:
        alert.target_price = update_data["target_price"]
    if "is_active" in update_data:
        alert.is_active = update_data["is_active"]
    alert.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert


def delete_stock_alert(db: Session, *, user_id: int, alert_id: int) -> bool:
    alert = db.query(StockPriceAlertORM).filter(StockPriceAlertORM.id == alert_id, StockPriceAlertORM.user_id == user_id).first()
    if not alert:
        return False
    db.delete(alert)
    db.commit()
    return True


def check_stock_alerts(db: Session, *, user_id: int) -> tuple[int, list[StockPriceAlertORM]]:
    alerts = (
        db.query(StockPriceAlertORM)
        .join(WatchlistORM, WatchlistORM.id == StockPriceAlertORM.watchlist_item_id)
        .filter(StockPriceAlertORM.user_id == user_id, StockPriceAlertORM.is_active.is_(True))
        .all()
    )
    now = datetime.now(timezone.utc)
    triggered: list[StockPriceAlertORM] = []

    for alert in alerts:
        item = alert.watchlist_item
        latest_price = Decimal(item.last_price) if item and item.last_price is not None else None
        alert.last_checked_at = now
        alert.updated_at = now
        if latest_price is None:
            continue

        should_trigger = (
            alert.condition_type == "above" and latest_price >= Decimal(alert.target_price)
        ) or (
            alert.condition_type == "below" and latest_price <= Decimal(alert.target_price)
        )
        if should_trigger:
            alert.triggered_at = now
            alert.last_price_at_trigger = latest_price
            alert.is_active = False
            triggered.append(alert)

    db.commit()
    for alert in triggered:
        db.refresh(alert)
    return len(alerts), triggered
