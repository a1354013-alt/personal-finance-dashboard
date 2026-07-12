from __future__ import annotations

from collections import Counter
from decimal import Decimal

from sqlalchemy.orm import Session

from models.stock import (
    PortfolioCurrencyGroupResponse,
    PortfolioPositionResponse,
    StockHoldingCreate,
    StockHoldingORM,
    StockHoldingResponse,
    StockHoldingUpdate,
    StockPortfolioResponse,
    WatchlistORM,
)
from services.stock_data_service import StockDataService
from services.watchlist_service import latest_history_for_code, latest_price_for_code

ZERO = Decimal("0")
HUNDRED = Decimal("100")


def _normalize_holding_currency(stock_code: str, currency: str | None) -> str:
    if currency:
        return currency.strip().upper()
    inferred = StockDataService.infer_currency(stock_code)
    return inferred or "USD"


def _latest_close_for_code(db: Session, stock_code: str) -> Decimal | None:
    latest_history = latest_history_for_code(db, stock_code=stock_code)
    if latest_history and latest_history.close is not None:
        return Decimal(latest_history.close)
    latest_price = latest_price_for_code(db, stock_code=stock_code)
    if latest_price and latest_price.close is not None:
        return Decimal(latest_price.close)
    return None


def _watchlist_name_by_code(db: Session, user_id: int) -> dict[str, str]:
    rows = db.query(WatchlistORM).filter(WatchlistORM.user_id == user_id).all()
    return {row.stock_code: (row.name or row.stock_code) for row in rows}


def list_holdings(db: Session, *, user_id: int) -> list[StockHoldingResponse]:
    rows = (
        db.query(StockHoldingORM)
        .filter(StockHoldingORM.user_id == user_id)
        .order_by(StockHoldingORM.stock_code.asc(), StockHoldingORM.id.asc())
        .all()
    )
    return [StockHoldingResponse.model_validate(row) for row in rows]


def create_holding(db: Session, *, user_id: int, payload: StockHoldingCreate) -> StockHoldingResponse:
    normalized_code = StockDataService.normalize_stock_code(payload.stock_code)
    row = StockHoldingORM(
        user_id=user_id,
        stock_code=normalized_code,
        shares=payload.shares,
        average_cost=payload.average_cost,
        currency=_normalize_holding_currency(normalized_code, payload.currency),
        note=payload.note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return StockHoldingResponse.model_validate(row)


def update_holding(
    db: Session,
    *,
    user_id: int,
    holding_id: int,
    payload: StockHoldingUpdate,
) -> StockHoldingResponse | None:
    row = db.query(StockHoldingORM).filter(StockHoldingORM.id == holding_id, StockHoldingORM.user_id == user_id).first()
    if not row:
        return None

    fields_set = payload.model_fields_set

    if "stock_code" in fields_set and payload.stock_code is not None:
        row.stock_code = StockDataService.normalize_stock_code(payload.stock_code)
    if "shares" in fields_set and payload.shares is not None:
        row.shares = payload.shares
    if "average_cost" in fields_set and payload.average_cost is not None:
        row.average_cost = payload.average_cost
    if "currency" in fields_set:
        row.currency = _normalize_holding_currency(row.stock_code, payload.currency)
    elif "stock_code" in fields_set and payload.stock_code is not None:
        row.currency = _normalize_holding_currency(row.stock_code, None)
    if "note" in fields_set:
        row.note = payload.note

    if not row.currency:
        row.currency = _normalize_holding_currency(row.stock_code, None)

    db.commit()
    db.refresh(row)
    return StockHoldingResponse.model_validate(row)


def delete_holding(db: Session, *, user_id: int, holding_id: int) -> bool:
    row = db.query(StockHoldingORM).filter(StockHoldingORM.id == holding_id, StockHoldingORM.user_id == user_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def build_portfolio_summary(db: Session, *, user_id: int) -> StockPortfolioResponse:
    holdings = (
        db.query(StockHoldingORM)
        .filter(StockHoldingORM.user_id == user_id)
        .order_by(StockHoldingORM.stock_code.asc(), StockHoldingORM.id.asc())
        .all()
    )
    if not holdings:
        return StockPortfolioResponse(total_cost=ZERO, holdings_count=0, currency=None, totals_by_currency=[], positions=[])

    names_by_code = _watchlist_name_by_code(db, user_id)
    currency_counts = Counter((row.currency or "").upper() for row in holdings if row.currency)
    distinct_currencies = sorted(currency_counts)
    portfolio_currency = distinct_currencies[0] if len(distinct_currencies) == 1 else None
    is_multi_currency = len(distinct_currencies) > 1
    warnings: list[str] = []
    positions: list[PortfolioPositionResponse] = []
    total_cost = ZERO
    total_market_value = ZERO
    priced_cost = ZERO
    missing_price_codes: list[str] = []
    totals_by_currency: dict[str, dict[str, Decimal | int]] = {}

    for row in holdings:
        shares = Decimal(row.shares)
        average_cost = Decimal(row.average_cost)
        cost_basis = shares * average_cost
        total_cost += cost_basis
        latest_price = _latest_close_for_code(db, row.stock_code)
        market_value = shares * latest_price if latest_price is not None else None
        unrealized_pnl = (market_value - cost_basis) if market_value is not None else None
        unrealized_pnl_percent = ((unrealized_pnl / cost_basis) * HUNDRED) if unrealized_pnl is not None and cost_basis else None
        position_currency = (row.currency or portfolio_currency or "USD").upper()

        group = totals_by_currency.setdefault(
            position_currency,
            {
                "total_cost": ZERO,
                "total_market_value": ZERO,
                "priced_cost": ZERO,
                "holdings_count": 0,
            },
        )
        group["total_cost"] = Decimal(group["total_cost"]) + cost_basis
        group["holdings_count"] = int(group["holdings_count"]) + 1

        if market_value is not None:
            total_market_value += market_value
            priced_cost += cost_basis
            group["total_market_value"] = Decimal(group["total_market_value"]) + market_value
            group["priced_cost"] = Decimal(group["priced_cost"]) + cost_basis
        else:
            missing_price_codes.append(row.stock_code)

        positions.append(
            PortfolioPositionResponse(
                holding_id=row.id,
                stock_code=row.stock_code,
                stock_name=names_by_code.get(row.stock_code, row.stock_code),
                shares=shares,
                average_cost=average_cost,
                latest_price=latest_price,
                cost_basis=cost_basis,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percent=unrealized_pnl_percent,
                allocation_percent=None,
                currency=position_currency,
                warning=f"Latest price unavailable for {row.stock_code}." if latest_price is None else None,
                updated_at=row.updated_at,
            )
        )

    if missing_price_codes:
        warnings.append(
            "Latest price unavailable for: " + ", ".join(sorted(missing_price_codes)) + ". Price-dependent fields are null."
        )

    if is_multi_currency:
        warnings.append(
            "Portfolio contains multiple currencies: "
            + ", ".join(distinct_currencies)
            + ". Totals are grouped by currency and are not FX-converted."
        )
    else:
        for position in positions:
            if position.market_value is not None and total_market_value > ZERO:
                position.allocation_percent = (position.market_value / total_market_value) * HUNDRED

    total_unrealized_pnl = total_market_value - priced_cost if total_market_value > ZERO or priced_cost > ZERO else ZERO
    total_unrealized_pnl_percent = (
        (total_unrealized_pnl / priced_cost) * HUNDRED if priced_cost > ZERO else None
    )
    grouped_totals = []
    for currency in sorted(totals_by_currency):
        group = totals_by_currency[currency]
        group_total_market_value = Decimal(group["total_market_value"])
        group_priced_cost = Decimal(group["priced_cost"])
        group_total_unrealized_pnl = (
            group_total_market_value - group_priced_cost if group_total_market_value > ZERO or group_priced_cost > ZERO else ZERO
        )
        group_total_unrealized_pnl_percent = (
            (group_total_unrealized_pnl / group_priced_cost) * HUNDRED if group_priced_cost > ZERO else None
        )
        grouped_totals.append(
            PortfolioCurrencyGroupResponse(
                currency=currency,
                total_cost=Decimal(group["total_cost"]),
                total_market_value=group_total_market_value if group_priced_cost > ZERO or group_total_market_value > ZERO else None,
                total_unrealized_pnl=group_total_unrealized_pnl if group_priced_cost > ZERO or group_total_market_value > ZERO else None,
                total_unrealized_pnl_percent=group_total_unrealized_pnl_percent,
                holdings_count=int(group["holdings_count"]),
            )
        )

    return StockPortfolioResponse(
        total_cost=total_cost if not is_multi_currency else None,
        total_market_value=total_market_value if not is_multi_currency and (priced_cost > ZERO or total_market_value > ZERO) else None,
        total_unrealized_pnl=total_unrealized_pnl if not is_multi_currency and (priced_cost > ZERO or total_market_value > ZERO) else None,
        total_unrealized_pnl_percent=total_unrealized_pnl_percent if not is_multi_currency else None,
        holdings_count=len(holdings),
        currency=portfolio_currency,
        warnings=warnings,
        totals_by_currency=grouped_totals,
        positions=positions,
    )
