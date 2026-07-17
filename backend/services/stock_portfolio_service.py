from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.stock import (
    PortfolioCurrencyTotalResponse,
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
HOLDING_UNIQUE_CONSTRAINT = "_user_stock_holding_uc"


def _normalize_holding_currency(stock_code: str, currency: str | None) -> str:
    if currency:
        return currency.strip().upper()
    inferred = StockDataService.infer_currency(stock_code)
    return inferred or "USD"


def _is_duplicate_holding_error(exc: IntegrityError) -> bool:
    text = str(exc.orig).lower()
    return (
        HOLDING_UNIQUE_CONSTRAINT.lower() in text
        or ("unique constraint failed" in text and "stock_holdings.user_id" in text and "stock_holdings.stock_code" in text)
        or ("duplicate key" in text and "stock_holdings" in text and "user_id" in text and "stock_code" in text)
    )


def _raise_duplicate_holding_error(exc: IntegrityError, stock_code: str) -> None:
    if not _is_duplicate_holding_error(exc):
        raise exc
    raise ValueError(
        f"A holding for {stock_code} already exists. Update the existing holding instead of creating a duplicate."
    ) from exc


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
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        _raise_duplicate_holding_error(exc, normalized_code)
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
    target_stock_code = row.stock_code

    stock_code_changed = False
    if "stock_code" in fields_set and payload.stock_code is not None:
        normalized_code = StockDataService.normalize_stock_code(payload.stock_code)
        target_stock_code = normalized_code
        stock_code_changed = normalized_code != row.stock_code
        row.stock_code = normalized_code
    if "shares" in fields_set and payload.shares is not None:
        row.shares = payload.shares
    if "average_cost" in fields_set and payload.average_cost is not None:
        row.average_cost = payload.average_cost
    if "currency" in fields_set:
        row.currency = _normalize_holding_currency(row.stock_code, payload.currency)
    elif stock_code_changed:
        row.currency = _normalize_holding_currency(row.stock_code, None)
    if "note" in fields_set:
        row.note = payload.note

    if not row.currency:
        row.currency = _normalize_holding_currency(row.stock_code, None)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        _raise_duplicate_holding_error(exc, target_stock_code)
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
        return StockPortfolioResponse(total_cost=ZERO, holdings_count=0, currency=None, currency_totals=[], positions=[])

    names_by_code = _watchlist_name_by_code(db, user_id)
    warnings: list[str] = []
    positions: list[PortfolioPositionResponse] = []
    totals_by_currency = defaultdict(
        lambda: {
            "total_cost": ZERO,
            "total_market_value": ZERO,
            "priced_cost": ZERO,
            "unpriced_cost": ZERO,
            "holdings_count": 0,
            "priced_holdings_count": 0,
            "missing_price_count": 0,
        }
    )
    missing_price_codes: list[str] = []

    for row in holdings:
        currency = (row.currency or _normalize_holding_currency(row.stock_code, None)).upper()
        shares = Decimal(row.shares)
        average_cost = Decimal(row.average_cost)
        cost_basis = shares * average_cost
        totals_by_currency[currency]["total_cost"] += cost_basis
        totals_by_currency[currency]["holdings_count"] += 1
        latest_price = _latest_close_for_code(db, row.stock_code)
        market_value = shares * latest_price if latest_price is not None else None
        unrealized_pnl = (market_value - cost_basis) if market_value is not None else None
        unrealized_pnl_percent = ((unrealized_pnl / cost_basis) * HUNDRED) if unrealized_pnl is not None and cost_basis else None

        if market_value is not None:
            totals_by_currency[currency]["total_market_value"] += market_value
            totals_by_currency[currency]["priced_cost"] += cost_basis
            totals_by_currency[currency]["priced_holdings_count"] += 1
        else:
            totals_by_currency[currency]["unpriced_cost"] += cost_basis
            totals_by_currency[currency]["missing_price_count"] += 1
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
                currency=currency,
                warning=f"Latest price unavailable for {row.stock_code}." if latest_price is None else None,
                updated_at=row.updated_at,
            )
        )

    if missing_price_codes:
        warnings.append(
            "Latest price unavailable for: " + ", ".join(sorted(missing_price_codes)) + ". Price-dependent fields are null."
        )

    currency_totals: list[PortfolioCurrencyTotalResponse] = []
    grouped_totals: list[PortfolioCurrencyGroupResponse] = []
    for currency in sorted(totals_by_currency):
        total_cost = Decimal(totals_by_currency[currency]["total_cost"])
        total_market_value = Decimal(totals_by_currency[currency]["total_market_value"])
        priced_cost = Decimal(totals_by_currency[currency]["priced_cost"])
        unpriced_cost = Decimal(totals_by_currency[currency]["unpriced_cost"])
        holdings_count = int(totals_by_currency[currency]["holdings_count"])
        priced_holdings_count = int(totals_by_currency[currency]["priced_holdings_count"])
        missing_price_count = int(totals_by_currency[currency]["missing_price_count"])
        has_priced_holdings = priced_cost > ZERO or total_market_value > ZERO
        total_unrealized_pnl = total_market_value - priced_cost if has_priced_holdings else None
        total_unrealized_pnl_percent = (
            (total_unrealized_pnl / priced_cost) * HUNDRED
            if total_unrealized_pnl is not None and priced_cost > ZERO
            else None
        )
        currency_totals.append(
            PortfolioCurrencyTotalResponse(
                currency=currency,
                total_cost=total_cost,
                total_market_value=total_market_value if has_priced_holdings else None,
                total_unrealized_pnl=total_unrealized_pnl,
                total_unrealized_pnl_percent=total_unrealized_pnl_percent,
                priced_cost=priced_cost,
                unpriced_cost=unpriced_cost,
                holdings_count=holdings_count,
                priced_holdings_count=priced_holdings_count,
                missing_price_count=missing_price_count,
                is_partial=missing_price_count > 0,
            )
        )
        grouped_totals.append(
            PortfolioCurrencyGroupResponse(
                currency=currency,
                total_cost=total_cost,
                total_market_value=total_market_value if has_priced_holdings else None,
                total_unrealized_pnl=total_unrealized_pnl,
                total_unrealized_pnl_percent=total_unrealized_pnl_percent,
                holdings_count=holdings_count,
            )
        )

    is_multi_currency = len(currency_totals) > 1
    if is_multi_currency:
        warnings.append(
            "Portfolio contains multiple currencies: "
            + ", ".join(item.currency for item in currency_totals)
            + ". Totals are grouped by currency and are not FX-converted."
        )
    else:
        market_value_by_currency = {item.currency: item.total_market_value for item in currency_totals}
        for position in positions:
            currency_market_value = market_value_by_currency.get(position.currency)
            if position.market_value is not None and currency_market_value is not None and currency_market_value > ZERO:
                position.allocation_percent = (position.market_value / currency_market_value) * HUNDRED

    single_currency_total = currency_totals[0] if len(currency_totals) == 1 else None

    return StockPortfolioResponse(
        total_cost=single_currency_total.total_cost if single_currency_total else None,
        total_market_value=single_currency_total.total_market_value if single_currency_total else None,
        total_unrealized_pnl=single_currency_total.total_unrealized_pnl if single_currency_total else None,
        total_unrealized_pnl_percent=single_currency_total.total_unrealized_pnl_percent if single_currency_total else None,
        holdings_count=len(holdings),
        currency=single_currency_total.currency if single_currency_total else None,
        currency_totals=currency_totals,
        warnings=warnings,
        totals_by_currency=grouped_totals,
        positions=positions,
    )
