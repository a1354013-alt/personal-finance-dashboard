from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date as DateType, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from models.stock import (
    StockHoldingCreate,
    StockHoldingORM,
    StockHoldingResponse,
    StockHoldingUpdate,
    StockTradeCreate,
    StockTradeORM,
    StockTradeResponse,
    StockTradeSummaryItem,
    StockTradeSummaryResponse,
    StockTradeUpdate,
)
from services.stock_data_service import StockDataService

ZERO = Decimal("0")
SHARE_PRECISION = Decimal("0.000001")
MONEY_PRECISION = Decimal("0.0001")
COMPATIBILITY_CONFLICT_MESSAGE = "This position is managed through its trade ledger."


class StockTradeError(ValueError):
    status_code = 400


class StockTradeConflictError(StockTradeError):
    status_code = 409


@dataclass
class ReplaySellResult:
    trade_id: int
    stock_code: str
    trade_date: DateType
    currency: str
    sold_shares: Decimal
    gross_proceeds: Decimal
    matched_cost_basis: Decimal
    fees: Decimal
    taxes: Decimal
    realized_pnl: Decimal


@dataclass
class ReplayOutcome:
    stock_code: str
    currency: str
    remaining_shares: Decimal
    remaining_cost_basis: Decimal
    average_cost: Decimal | None
    opening_note: str | None
    realized_sales: list[ReplaySellResult]


def _quantize_shares(value: Decimal) -> Decimal:
    return Decimal(value).quantize(SHARE_PRECISION, rounding=ROUND_HALF_UP)


def _quantize_money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def _normalize_currency(stock_code: str, currency: str | None) -> str:
    if currency:
        normalized = currency.strip().upper()
        if normalized:
            return normalized[:10]
    inferred = StockDataService.infer_currency(stock_code)
    return inferred or "USD"


def _ordered_trade_query(db: Session, *, user_id: int, stock_code: str):
    return (
        db.query(StockTradeORM)
        .filter(StockTradeORM.user_id == user_id, StockTradeORM.stock_code == stock_code)
        .order_by(StockTradeORM.trade_date.asc(), StockTradeORM.created_at.asc(), StockTradeORM.id.asc())
    )


def _load_trades_for_replay(db: Session, *, user_id: int, stock_code: str) -> list[StockTradeORM]:
    return _ordered_trade_query(db, user_id=user_id, stock_code=stock_code).all()


def _replay_trades(trades: list[StockTradeORM]) -> ReplayOutcome:
    if not trades:
        raise StockTradeError("No trades available for replay.")

    lots: list[dict[str, Decimal]] = []
    realized_sales: list[ReplaySellResult] = []
    opening_note: str | None = None
    currency = trades[0].currency
    mixed_currencies = {str(trade.currency or "").upper() for trade in trades}
    if len(mixed_currencies) != 1:
        stock_code = trades[0].stock_code
        raise StockTradeConflictError(f"Trade ledger for {stock_code} contains mixed currencies and cannot be replayed.")

    for trade in trades:
        shares = _quantize_shares(Decimal(trade.shares))
        price = _quantize_money(Decimal(trade.price))
        fee = _quantize_money(Decimal(trade.fee or ZERO))
        tax = _quantize_money(Decimal(trade.tax or ZERO))
        if trade.trade_type == "OPENING_BALANCE" and opening_note is None:
            opening_note = trade.note

        if trade.trade_type in {"OPENING_BALANCE", "BUY"}:
            total_cost = _quantize_money((shares * price) + fee)
            lots.append(
                {
                    "remaining_shares": shares,
                    "remaining_cost": total_cost,
                }
            )
            continue

        shares_to_sell = shares
        matched_cost_basis = ZERO
        while shares_to_sell > ZERO:
            if not lots:
                raise StockTradeConflictError(
                    f"Trade replay would create negative inventory for {trade.stock_code} on {trade.trade_date.isoformat()}."
                )
            lot = lots[0]
            lot_shares = lot["remaining_shares"]
            consume_shares = shares_to_sell if shares_to_sell < lot_shares else lot_shares
            if consume_shares == lot_shares:
                consumed_cost = lot["remaining_cost"]
                lots.pop(0)
            else:
                consumed_cost = _quantize_money(lot["remaining_cost"] * (consume_shares / lot_shares))
                lot["remaining_shares"] = _quantize_shares(lot_shares - consume_shares)
                lot["remaining_cost"] = _quantize_money(lot["remaining_cost"] - consumed_cost)
            matched_cost_basis += consumed_cost
            shares_to_sell = _quantize_shares(shares_to_sell - consume_shares)

        gross_proceeds = _quantize_money(shares * price)
        net_proceeds = _quantize_money(gross_proceeds - fee - tax)
        matched_cost_basis = _quantize_money(matched_cost_basis)
        realized_sales.append(
            ReplaySellResult(
                trade_id=trade.id,
                stock_code=trade.stock_code,
                trade_date=trade.trade_date,
                currency=currency,
                sold_shares=shares,
                gross_proceeds=gross_proceeds,
                matched_cost_basis=matched_cost_basis,
                fees=fee,
                taxes=tax,
                realized_pnl=_quantize_money(net_proceeds - matched_cost_basis),
            )
        )

    remaining_shares = _quantize_shares(sum(lot["remaining_shares"] for lot in lots))
    remaining_cost_basis = _quantize_money(sum(lot["remaining_cost"] for lot in lots))
    average_cost = _quantize_money(remaining_cost_basis / remaining_shares) if remaining_shares > ZERO else None
    return ReplayOutcome(
        stock_code=trades[0].stock_code,
        currency=currency,
        remaining_shares=remaining_shares,
        remaining_cost_basis=remaining_cost_basis,
        average_cost=average_cost,
        opening_note=opening_note,
        realized_sales=realized_sales,
    )


def rebuild_stock_holding_projection(db: Session, user_id: int, stock_code: str) -> StockHoldingORM | None:
    normalized_code = StockDataService.normalize_stock_code(stock_code)
    trades = _load_trades_for_replay(db, user_id=user_id, stock_code=normalized_code)
    existing = (
        db.query(StockHoldingORM)
        .filter(StockHoldingORM.user_id == user_id, StockHoldingORM.stock_code == normalized_code)
        .first()
    )
    if not trades:
        if existing:
            db.delete(existing)
            db.flush()
        return None

    outcome = _replay_trades(trades)
    if outcome.remaining_shares <= ZERO:
        if existing:
            db.delete(existing)
            db.flush()
        return None

    if existing is None:
        existing = StockHoldingORM(user_id=user_id, stock_code=normalized_code)
        db.add(existing)

    existing.shares = outcome.remaining_shares
    existing.average_cost = outcome.average_cost or ZERO
    existing.currency = outcome.currency
    existing.note = outcome.opening_note
    existing.updated_at = datetime.now(timezone.utc)
    db.flush()
    return existing


def list_trades(
    db: Session,
    *,
    user_id: int,
    stock_code: str | None = None,
    trade_type: str | None = None,
    date_from: DateType | None = None,
    date_to: DateType | None = None,
) -> list[StockTradeResponse]:
    query = db.query(StockTradeORM).filter(StockTradeORM.user_id == user_id)
    if stock_code:
        query = query.filter(StockTradeORM.stock_code == StockDataService.normalize_stock_code(stock_code))
    if trade_type:
        query = query.filter(StockTradeORM.trade_type == trade_type)
    if date_from:
        query = query.filter(StockTradeORM.trade_date >= date_from)
    if date_to:
        query = query.filter(StockTradeORM.trade_date <= date_to)
    rows = query.order_by(StockTradeORM.trade_date.desc(), StockTradeORM.created_at.desc(), StockTradeORM.id.desc()).all()
    return [StockTradeResponse.model_validate(row) for row in rows]


def _currency_conflict_exists(
    db: Session,
    *,
    user_id: int,
    stock_code: str,
    currency: str,
    exclude_trade_id: int | None = None,
) -> bool:
    query = db.query(StockTradeORM).filter(
        StockTradeORM.user_id == user_id,
        StockTradeORM.stock_code == stock_code,
        StockTradeORM.currency != currency,
    )
    if exclude_trade_id is not None:
        query = query.filter(StockTradeORM.id != exclude_trade_id)
    return query.first() is not None


def _opening_balance_conflict_exists(
    db: Session,
    *,
    user_id: int,
    stock_code: str,
    exclude_trade_id: int | None = None,
) -> bool:
    query = db.query(StockTradeORM).filter(
        StockTradeORM.user_id == user_id,
        StockTradeORM.stock_code == stock_code,
        StockTradeORM.trade_type == "OPENING_BALANCE",
    )
    if exclude_trade_id is not None:
        query = query.filter(StockTradeORM.id != exclude_trade_id)
    return query.first() is not None


def _symbol_has_trade_history(
    db: Session,
    *,
    user_id: int,
    stock_code: str,
    exclude_trade_id: int | None = None,
) -> bool:
    normalized_code = StockDataService.normalize_stock_code(stock_code)
    query = db.query(StockTradeORM).filter(
        StockTradeORM.user_id == user_id,
        StockTradeORM.stock_code == normalized_code,
    )
    if exclude_trade_id is not None:
        query = query.filter(StockTradeORM.id != exclude_trade_id)
    return query.first() is not None


def _ensure_symbol_trade_invariants(
    db: Session,
    *,
    user_id: int,
    stock_code: str,
    currency: str,
    trade_type: str,
    exclude_trade_id: int | None = None,
) -> None:
    if _currency_conflict_exists(db, user_id=user_id, stock_code=stock_code, currency=currency, exclude_trade_id=exclude_trade_id):
        raise StockTradeConflictError(f"Trade ledger for {stock_code} already uses a different currency.")
    if trade_type == "OPENING_BALANCE" and _opening_balance_conflict_exists(
        db,
        user_id=user_id,
        stock_code=stock_code,
        exclude_trade_id=exclude_trade_id,
    ):
        raise StockTradeConflictError(f"Trade ledger for {stock_code} already has an opening balance.")


def _apply_trade_payload(row: StockTradeORM, payload: StockTradeCreate | StockTradeUpdate) -> tuple[str, str]:
    original_code = row.stock_code
    fields_set = payload.model_fields_set if isinstance(payload, StockTradeUpdate) else None
    original_currency = row.currency

    def wants(name: str) -> bool:
        return fields_set is None or name in fields_set

    if wants("stock_code") and payload.stock_code is not None:
        row.stock_code = StockDataService.normalize_stock_code(payload.stock_code)
    if wants("trade_type") and getattr(payload, "trade_type", None) is not None:
        row.trade_type = payload.trade_type
    if wants("trade_date") and payload.trade_date is not None:
        row.trade_date = payload.trade_date
    if wants("shares") and payload.shares is not None:
        row.shares = _quantize_shares(payload.shares)
    if wants("price") and payload.price is not None:
        row.price = _quantize_money(payload.price)
    if wants("fee") and payload.fee is not None:
        row.fee = _quantize_money(payload.fee)
    if wants("tax") and payload.tax is not None:
        row.tax = _quantize_money(payload.tax)
    if wants("currency"):
        row.currency = _normalize_currency(row.stock_code, payload.currency)
    elif row.stock_code != original_code:
        row.currency = _normalize_currency(row.stock_code, None)
    else:
        row.currency = original_currency
    if wants("note"):
        row.note = payload.note
    row.updated_at = datetime.now(timezone.utc)
    return original_code, row.stock_code


def _commit_trade_change(db: Session, *, user_id: int, affected_codes: set[str]) -> None:
    try:
        for code in sorted(affected_codes):
            rebuild_stock_holding_projection(db, user_id, code)
        db.commit()
    except Exception:
        db.rollback()
        raise


def _create_trade_row(
    db: Session,
    *,
    user_id: int,
    payload: StockTradeCreate,
    source: str | None = None,
    source_holding_id: int | None = None,
) -> StockTradeORM:
    normalized_code = StockDataService.normalize_stock_code(payload.stock_code)
    currency = _normalize_currency(normalized_code, payload.currency)
    _ensure_symbol_trade_invariants(db, user_id=user_id, stock_code=normalized_code, currency=currency, trade_type=payload.trade_type)
    row = StockTradeORM(
        user_id=user_id,
        stock_code=normalized_code,
        trade_type=payload.trade_type,
        trade_date=payload.trade_date,
        shares=_quantize_shares(payload.shares),
        price=_quantize_money(payload.price),
        fee=_quantize_money(payload.fee),
        tax=_quantize_money(payload.tax),
        currency=currency,
        note=payload.note,
        source=source,
        source_holding_id=source_holding_id,
    )
    db.add(row)
    db.flush()
    return row


def create_trade(db: Session, *, user_id: int, payload: StockTradeCreate) -> StockTradeResponse:
    if payload.trade_type == "OPENING_BALANCE":
        raise StockTradeConflictError("Opening balances must be created through the holdings endpoint.")
    row = _create_trade_row(db, user_id=user_id, payload=payload)
    _commit_trade_change(db, user_id=user_id, affected_codes={row.stock_code})
    db.refresh(row)
    return StockTradeResponse.model_validate(row)


def update_trade(db: Session, *, user_id: int, trade_id: int, payload: StockTradeUpdate) -> StockTradeResponse | None:
    row = db.query(StockTradeORM).filter(StockTradeORM.id == trade_id, StockTradeORM.user_id == user_id).first()
    if row is None:
        return None
    original_code, new_code = _apply_trade_payload(row, payload)
    _ensure_symbol_trade_invariants(
        db,
        user_id=user_id,
        stock_code=new_code,
        currency=row.currency,
        trade_type=row.trade_type,
        exclude_trade_id=row.id,
    )
    db.flush()
    _commit_trade_change(db, user_id=user_id, affected_codes={original_code, new_code})
    db.refresh(row)
    return StockTradeResponse.model_validate(row)


def delete_trade(db: Session, *, user_id: int, trade_id: int) -> bool:
    row = db.query(StockTradeORM).filter(StockTradeORM.id == trade_id, StockTradeORM.user_id == user_id).first()
    if row is None:
        return False
    affected_code = row.stock_code
    db.delete(row)
    db.flush()
    _commit_trade_change(db, user_id=user_id, affected_codes={affected_code})
    return True


def _symbol_has_non_opening_trades(db: Session, *, user_id: int, stock_code: str) -> bool:
    normalized_code = StockDataService.normalize_stock_code(stock_code)
    return (
        db.query(StockTradeORM)
        .filter(
            StockTradeORM.user_id == user_id,
            StockTradeORM.stock_code == normalized_code,
            StockTradeORM.trade_type.in_(["BUY", "SELL"]),
        )
        .first()
        is not None
    )


def _get_opening_trade(db: Session, *, user_id: int, stock_code: str, source_holding_id: int | None = None) -> StockTradeORM | None:
    normalized_code = StockDataService.normalize_stock_code(stock_code)
    query = db.query(StockTradeORM).filter(
        StockTradeORM.user_id == user_id,
        StockTradeORM.stock_code == normalized_code,
        StockTradeORM.trade_type == "OPENING_BALANCE",
    )
    if source_holding_id is not None:
        query = query.filter(StockTradeORM.source_holding_id == source_holding_id)
    return query.order_by(StockTradeORM.trade_date.asc(), StockTradeORM.created_at.asc(), StockTradeORM.id.asc()).first()


def create_or_update_opening_balance(
    db: Session,
    *,
    user_id: int,
    payload: StockHoldingCreate,
) -> StockHoldingResponse:
    normalized_code = StockDataService.normalize_stock_code(payload.stock_code)
    opening = _get_opening_trade(db, user_id=user_id, stock_code=normalized_code)
    if opening is not None:
        raise StockTradeConflictError(
            f"A holding for {normalized_code} already exists. Update the existing holding instead of creating a duplicate."
        )
    if _symbol_has_trade_history(db, user_id=user_id, stock_code=normalized_code):
        raise StockTradeConflictError(COMPATIBILITY_CONFLICT_MESSAGE)
    if opening is None:
        row = _create_trade_row(
            db,
            user_id=user_id,
            payload=StockTradeCreate(
                stock_code=normalized_code,
                trade_type="OPENING_BALANCE",
                trade_date=DateType.today(),
                shares=payload.shares,
                price=payload.average_cost,
                fee=ZERO,
                tax=ZERO,
                currency=payload.currency,
                note=payload.note,
            ),
            source="legacy_holding",
        )
        _commit_trade_change(db, user_id=user_id, affected_codes={row.stock_code})
        created = StockTradeResponse.model_validate(row)
        row = (
            db.query(StockHoldingORM)
            .filter(StockHoldingORM.user_id == user_id, StockHoldingORM.stock_code == created.stock_code)
            .one()
        )
        db.query(StockTradeORM).filter(StockTradeORM.id == created.id).update({"source_holding_id": row.id})
        db.commit()
        db.refresh(row)
        return StockHoldingResponse.model_validate(row)
    raise StockTradeError(
        f"A holding for {normalized_code} already exists. Update the existing holding instead of creating a duplicate."
    )


def update_legacy_holding(
    db: Session,
    *,
    user_id: int,
    holding_id: int,
    payload: StockHoldingUpdate,
) -> StockHoldingResponse | None:
    holding = db.query(StockHoldingORM).filter(StockHoldingORM.id == holding_id, StockHoldingORM.user_id == user_id).first()
    if holding is None:
        return None
    if _symbol_has_non_opening_trades(db, user_id=user_id, stock_code=holding.stock_code):
        raise StockTradeConflictError(COMPATIBILITY_CONFLICT_MESSAGE)
    opening = _get_opening_trade(db, user_id=user_id, stock_code=holding.stock_code, source_holding_id=holding.id) or _get_opening_trade(
        db, user_id=user_id, stock_code=holding.stock_code
    )
    if opening is None:
        raise StockTradeError("Legacy opening balance trade not found for this holding.")

    next_code = StockDataService.normalize_stock_code(payload.stock_code) if payload.stock_code is not None else holding.stock_code
    if next_code != holding.stock_code and _symbol_has_trade_history(db, user_id=user_id, stock_code=next_code, exclude_trade_id=opening.id):
        raise StockTradeConflictError(f"Cannot rename holding to {next_code} because that symbol already has trade history.")
    duplicate_opening = _get_opening_trade(db, user_id=user_id, stock_code=next_code)
    if duplicate_opening is not None and duplicate_opening.id != opening.id:
        raise StockTradeError(
            f"A holding for {next_code} already exists. Update the existing holding instead of creating a duplicate."
        )
    if "currency" in payload.model_fields_set:
        next_currency = payload.currency
    elif next_code != holding.stock_code:
        next_currency = None
    else:
        next_currency = holding.currency
    next_shares = payload.shares if payload.shares is not None else Decimal(holding.shares)
    next_average_cost = payload.average_cost if payload.average_cost is not None else Decimal(holding.average_cost)
    next_note = payload.note if "note" in payload.model_fields_set else holding.note
    normalized_currency = _normalize_currency(next_code, next_currency)
    timestamp = datetime.now(timezone.utc)

    original_code = holding.stock_code
    opening.stock_code = next_code
    opening.shares = _quantize_shares(next_shares)
    opening.price = _quantize_money(next_average_cost)
    opening.fee = ZERO
    opening.tax = ZERO
    opening.currency = normalized_currency
    opening.note = next_note
    opening.updated_at = timestamp

    try:
        db.flush()
        rebuild_stock_holding_projection(db, user_id, original_code)
        rebuild_stock_holding_projection(db, user_id, next_code)
        db.commit()
    except Exception:
        db.rollback()
        raise
    projected = (
        db.query(StockHoldingORM)
        .filter(StockHoldingORM.user_id == user_id, StockHoldingORM.stock_code == next_code)
        .one()
    )
    return StockHoldingResponse.model_validate(projected)


def delete_legacy_holding(db: Session, *, user_id: int, holding_id: int) -> bool:
    holding = db.query(StockHoldingORM).filter(StockHoldingORM.id == holding_id, StockHoldingORM.user_id == user_id).first()
    if holding is None:
        return False
    if _symbol_has_non_opening_trades(db, user_id=user_id, stock_code=holding.stock_code):
        raise StockTradeConflictError(COMPATIBILITY_CONFLICT_MESSAGE)
    opening = _get_opening_trade(db, user_id=user_id, stock_code=holding.stock_code, source_holding_id=holding.id) or _get_opening_trade(
        db, user_id=user_id, stock_code=holding.stock_code
    )
    if opening is None:
        return False
    affected_code = opening.stock_code
    db.delete(opening)
    db.flush()
    _commit_trade_change(db, user_id=user_id, affected_codes={affected_code})
    return True


def summarize_trades(
    db: Session,
    *,
    user_id: int,
    stock_code: str | None = None,
    trade_type: str | None = None,
    date_from: DateType | None = None,
    date_to: DateType | None = None,
) -> StockTradeSummaryResponse:
    selected_query = db.query(StockTradeORM).filter(StockTradeORM.user_id == user_id)
    replay_query = db.query(StockTradeORM).filter(StockTradeORM.user_id == user_id)
    if stock_code:
        normalized_code = StockDataService.normalize_stock_code(stock_code)
        selected_query = selected_query.filter(StockTradeORM.stock_code == normalized_code)
        replay_query = replay_query.filter(StockTradeORM.stock_code == normalized_code)
    if trade_type:
        selected_query = selected_query.filter(StockTradeORM.trade_type == trade_type)
    if date_from:
        selected_query = selected_query.filter(StockTradeORM.trade_date >= date_from)
    if date_to:
        selected_query = selected_query.filter(StockTradeORM.trade_date <= date_to)
        replay_query = replay_query.filter(StockTradeORM.trade_date <= date_to)
    selected_trades = selected_query.order_by(
        StockTradeORM.stock_code.asc(),
        StockTradeORM.trade_date.asc(),
        StockTradeORM.created_at.asc(),
        StockTradeORM.id.asc(),
    ).all()
    selected_trade_ids = {trade.id for trade in selected_trades}
    grouped: dict[str, list[StockTradeORM]] = defaultdict(list)
    for trade in replay_query.order_by(
        StockTradeORM.stock_code.asc(),
        StockTradeORM.trade_date.asc(),
        StockTradeORM.created_at.asc(),
        StockTradeORM.id.asc(),
    ).all():
        grouped[trade.stock_code].append(trade)

    totals = defaultdict(
        lambda: {
            "buy_count": 0,
            "sell_count": 0,
            "opening_balance_count": 0,
            "opening_balance_shares": ZERO,
            "bought_shares": ZERO,
            "sold_shares": ZERO,
            "gross_proceeds": ZERO,
            "matched_cost_basis": ZERO,
            "fees": ZERO,
            "taxes": ZERO,
            "realized_pnl": ZERO,
        }
    )

    for symbol_trades in grouped.values():
        outcome = _replay_trades(symbol_trades)
        currency = outcome.currency
        for trade in selected_trades:
            if trade.stock_code != outcome.stock_code:
                continue
            shares = _quantize_shares(Decimal(trade.shares))
            fee = _quantize_money(Decimal(trade.fee or ZERO))
            tax = _quantize_money(Decimal(trade.tax or ZERO))
            totals[currency]["fees"] += fee
            totals[currency]["taxes"] += tax
            if trade.trade_type == "OPENING_BALANCE":
                totals[currency]["opening_balance_count"] += 1
                totals[currency]["opening_balance_shares"] += shares
            elif trade.trade_type == "BUY":
                totals[currency]["buy_count"] += 1
                totals[currency]["bought_shares"] += shares
            elif trade.trade_type == "SELL":
                totals[currency]["sell_count"] += 1
                totals[currency]["sold_shares"] += shares
        for sale in outcome.realized_sales:
            if sale.trade_id not in selected_trade_ids:
                continue
            totals[currency]["gross_proceeds"] += sale.gross_proceeds
            totals[currency]["matched_cost_basis"] += sale.matched_cost_basis
            totals[currency]["realized_pnl"] += sale.realized_pnl

    items = [
        StockTradeSummaryItem(
            currency=currency,
            opening_balance_count=int(values["opening_balance_count"]),
            opening_balance_shares=_quantize_shares(values["opening_balance_shares"]),
            buy_count=int(values["buy_count"]),
            sell_count=int(values["sell_count"]),
            bought_shares=_quantize_shares(values["bought_shares"]),
            sold_shares=_quantize_shares(values["sold_shares"]),
            gross_proceeds=_quantize_money(values["gross_proceeds"]),
            matched_cost_basis=_quantize_money(values["matched_cost_basis"]),
            fees=_quantize_money(values["fees"]),
            taxes=_quantize_money(values["taxes"]),
            realized_pnl=_quantize_money(values["realized_pnl"]),
        )
        for currency, values in sorted(totals.items())
    ]
    return StockTradeSummaryResponse(items=items)
