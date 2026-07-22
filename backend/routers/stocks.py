from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.jobs.job_runner import JOB_TYPE_SYNC_STOCK_MARKET_DATA
from db.database import get_db
from models.fundamentals import FundamentalsSnapshot, FundamentalsSyncOptions
from models.job import CreateJobRequest
from models.stock import (
    StockHoldingCreate,
    StockHoldingResponse,
    StockHoldingUpdate,
    StockAIAnalysisResponse,
    StockDashboardResponse,
    StockFilterRequest,
    StockFilterResult,
    StockIndicatorsResponse,
    StockPortfolioResponse,
    StockTradeCreate,
    StockTradeResponse,
    StockTradeSummaryResponse,
    StockTradeType,
    StockTradeUpdate,
    StockPriceAlertCheckResponse,
    StockPriceAlertCreate,
    StockPriceAlertResponse,
    StockPriceAlertUpdate,
    StockPriceHistoryPoint,
    WatchlistCreate,
    WatchlistItemResponse,
    WatchlistORM,
)
from models.stocks_filter import FilterMetadataResponse, StockFundamentalsFilterResult
from models.user import UserORM
from services.auth import get_current_user
from services.fundamentals_service import get_latest_fundamentals_by_code, queue_fundamentals_sync
from services.job_service import create_job, find_active_job_by_payload
from services.stock_data_service import StockDataService
from services.stock_filter import evaluate_stock
from services.stock_alert_service import (
    check_stock_alerts,
    create_stock_alert,
    delete_stock_alert,
    list_stock_alerts,
    update_stock_alert,
)
from services.stock_ai_analysis_service import build_stock_ai_analysis
from services.stock_indicator_service import build_stock_indicators
from services.stock_portfolio_service import build_portfolio_summary, create_holding, delete_holding, list_holdings, update_holding
from services.stock_trade_service import (
    StockTradeConflictError,
    StockTradeError,
    create_trade,
    delete_trade,
    list_trades,
    summarize_trades,
    update_trade,
)
from services.stocks_ai_explanation_service import build_stock_ai_explanation
from services.stocks_fundamentals_screening_service import build_filter_metadata, build_filter_results
from services.watchlist_service import (
    SYNC_STATUS_PENDING,
    build_watchlist_item,
    create_watchlist_item,
    delete_watchlist_item,
    list_watchlist,
    update_watchlist_sync_status,
    sync_watchlist_item_now,
)

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])


def _validate_trade_date_range(date_from: date | None, date_to: date | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="date_from must be on or before date_to.")


def _queue_price_sync_job(
    db: Session,
    *,
    watchlist_item: WatchlistORM,
    request_id: str | None,
):
    job_payload = {
        "user_id": watchlist_item.user_id,
        "watchlist_item_id": watchlist_item.id,
        "stock_code": watchlist_item.stock_code,
    }
    existing_job = find_active_job_by_payload(
        db,
        job_type=JOB_TYPE_SYNC_STOCK_MARKET_DATA,
        expected_payload={
            "user_id": watchlist_item.user_id,
            "watchlist_item_id": watchlist_item.id,
            "stock_code": watchlist_item.stock_code,
        },
    )
    if existing_job:
        return existing_job
    return create_job(
        db,
        CreateJobRequest(
            job_type=JOB_TYPE_SYNC_STOCK_MARKET_DATA,
            payload=job_payload,
            request_id=request_id,
        ),
    )


@router.get("/watchlist", response_model=list[WatchlistItemResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return list_watchlist(db, user_id=current_user.id)


@router.get("/holdings", response_model=list[StockHoldingResponse])
def get_stock_holdings(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return list_holdings(db, user_id=current_user.id)


@router.post("/holdings", response_model=StockHoldingResponse, status_code=status.HTTP_201_CREATED)
def create_stock_holding(
    payload: StockHoldingCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    try:
        return create_holding(db, user_id=current_user.id, payload=payload)
    except StockTradeConflictError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/holdings/{holding_id}", response_model=StockHoldingResponse)
def update_stock_holding(
    holding_id: int,
    payload: StockHoldingUpdate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    try:
        updated = update_holding(db, user_id=current_user.id, holding_id=holding_id, payload=payload)
    except StockTradeConflictError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock holding not found.")
    return updated


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock_holding(
    holding_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    try:
        ok = delete_holding(db, user_id=current_user.id, holding_id=holding_id)
    except StockTradeConflictError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock holding not found.")


@router.get("/portfolio", response_model=StockPortfolioResponse)
def get_stock_portfolio(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return build_portfolio_summary(db, user_id=current_user.id)


@router.get("/trades", response_model=list[StockTradeResponse])
def get_stock_trades(
    stock_code: str | None = None,
    trade_type: StockTradeType | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    _validate_trade_date_range(date_from, date_to)
    return list_trades(
        db,
        user_id=current_user.id,
        stock_code=stock_code,
        trade_type=trade_type,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/trades", response_model=StockTradeResponse, status_code=status.HTTP_201_CREATED)
def create_stock_trade(
    payload: StockTradeCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    try:
        return create_trade(db, user_id=current_user.id, payload=payload)
    except StockTradeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.put("/trades/{trade_id}", response_model=StockTradeResponse)
def update_stock_trade(
    trade_id: int,
    payload: StockTradeUpdate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    try:
        updated = update_trade(db, user_id=current_user.id, trade_id=trade_id, payload=payload)
    except StockTradeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock trade not found.")
    return updated


@router.delete("/trades/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    try:
        ok = delete_trade(db, user_id=current_user.id, trade_id=trade_id)
    except StockTradeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock trade not found.")


@router.get("/trades/summary", response_model=StockTradeSummaryResponse)
def get_stock_trade_summary(
    stock_code: str | None = None,
    trade_type: StockTradeType | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    _validate_trade_date_range(date_from, date_to)
    try:
        return summarize_trades(
            db,
            user_id=current_user.id,
            stock_code=stock_code,
            trade_type=trade_type,
            date_from=date_from,
            date_to=date_to,
        )
    except StockTradeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/watchlist", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    request: WatchlistCreate,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    try:
        new_item = create_watchlist_item(db, user_id=current_user.id, stock_code=request.stock_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    update_watchlist_sync_status(
        db,
        watchlist_item_id=new_item.id,
        user_id=current_user.id,
        status=SYNC_STATUS_PENDING,
        error_message="Market data sync queued.",
    )
    _queue_price_sync_job(
        db,
        watchlist_item=new_item,
        request_id=getattr(http_request.state, "request_id", None),
    )
    refreshed_item = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.id == new_item.id, WatchlistORM.user_id == current_user.id)
        .first()
    )
    return build_watchlist_item(db, item=refreshed_item)


@router.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_from_watchlist(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    ok = delete_watchlist_item(db, user_id=current_user.id, item_id=item_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")


@router.post("/watchlist/{item_id}/sync", response_model=WatchlistItemResponse)
def sync_watchlist_item_price(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist_item = (
        db.query(WatchlistORM).filter(WatchlistORM.id == item_id, WatchlistORM.user_id == current_user.id).first()
    )
    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")

    sync_watchlist_item_now(db, watchlist_item=watchlist_item)
    db.refresh(watchlist_item)
    return build_watchlist_item(db, item=watchlist_item)


@router.get("/watchlist/{item_id}/indicators", response_model=StockIndicatorsResponse)
def get_watchlist_item_indicators(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist_item = (
        db.query(WatchlistORM).filter(WatchlistORM.id == item_id, WatchlistORM.user_id == current_user.id).first()
    )
    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")
    return build_stock_indicators(db, watchlist_item=watchlist_item)


@router.get("/alerts", response_model=list[StockPriceAlertResponse])
def get_stock_alerts(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return list_stock_alerts(db, user_id=current_user.id)


@router.post("/watchlist/{item_id}/alerts", response_model=StockPriceAlertResponse, status_code=status.HTTP_201_CREATED)
def create_watchlist_item_alert(
    item_id: int,
    payload: StockPriceAlertCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist_item = (
        db.query(WatchlistORM).filter(WatchlistORM.id == item_id, WatchlistORM.user_id == current_user.id).first()
    )
    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")
    return create_stock_alert(
        db,
        user_id=current_user.id,
        watchlist_item=watchlist_item,
        condition_type=payload.condition_type,
        target_price=payload.target_price,
    )


@router.put("/alerts/{alert_id}", response_model=StockPriceAlertResponse)
def update_existing_stock_alert(
    alert_id: int,
    payload: StockPriceAlertUpdate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    alert = update_stock_alert(db, user_id=current_user.id, alert_id=alert_id, payload=payload)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock alert not found.")
    return alert


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_stock_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    ok = delete_stock_alert(db, user_id=current_user.id, alert_id=alert_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock alert not found.")


@router.post("/alerts/check", response_model=StockPriceAlertCheckResponse)
def check_existing_stock_alerts(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    checked_count, triggered = check_stock_alerts(db, user_id=current_user.id)
    return {"checked_count": checked_count, "triggered_count": len(triggered), "alerts": triggered}


@router.post("/watchlist/{item_id}/ai-analysis", response_model=StockAIAnalysisResponse)
def analyze_watchlist_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist_item = (
        db.query(WatchlistORM).filter(WatchlistORM.id == item_id, WatchlistORM.user_id == current_user.id).first()
    )
    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")
    return build_stock_ai_analysis(db, watchlist_item=watchlist_item)


@router.post("/fundamentals/sync", response_model=list[FundamentalsSnapshot])
def sync_watchlist_fundamentals(
    payload: FundamentalsSyncOptions,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    rows = [
        queue_fundamentals_sync(
            db,
            user_id=current_user.id,
            stock_code=item.stock_code,
            request_id=getattr(request.state, "request_id", None),
            force=payload.force,
        )
        for item in watchlist
    ]
    return [FundamentalsSnapshot.model_validate(row) for row in rows]


@router.post("/fundamentals/{stock_code}/sync", response_model=FundamentalsSnapshot)
def sync_single_fundamentals(
    stock_code: str,
    payload: FundamentalsSyncOptions,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    formatted_code = StockDataService.normalize_stock_code(stock_code)
    watchlist_item = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.user_id == current_user.id, WatchlistORM.stock_code == formatted_code)
        .first()
    )
    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")

    row = queue_fundamentals_sync(
        db,
        user_id=current_user.id,
        stock_code=formatted_code,
        request_id=getattr(request.state, "request_id", None),
        force=payload.force,
    )
    return FundamentalsSnapshot.model_validate(row)


@router.get("/fundamentals", response_model=list[FundamentalsSnapshot])
def get_watchlist_fundamentals(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    codes = {item.stock_code for item in watchlist}
    latest = get_latest_fundamentals_by_code(db, codes)
    return [FundamentalsSnapshot.model_validate(latest[code]) for code in sorted(latest)]


@router.get("/history/{stock_code}", response_model=list[StockPriceHistoryPoint])
def get_stock_history(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    formatted_code = StockDataService.normalize_stock_code(stock_code)
    exists = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.user_id == current_user.id, WatchlistORM.stock_code == formatted_code)
        .first()
    )
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")

    from models.stock import StockPriceHistoryORM

    rows = (
        db.query(StockPriceHistoryORM)
        .filter(StockPriceHistoryORM.stock_code == formatted_code)
        .order_by(StockPriceHistoryORM.trade_date.asc())
        .all()
    )
    return [StockPriceHistoryPoint.model_validate(row) for row in rows]


@router.get("/dashboard", response_model=StockDashboardResponse)
def get_stock_dashboard(
    request: Request,
    selected_code: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist = list_watchlist(db, user_id=current_user.id)
    if not watchlist:
        return StockDashboardResponse(watchlist=[], price_history=[], fundamentals=None, ai_explanation=None)

    selected_stock_code = StockDataService.normalize_stock_code(selected_code or watchlist[0]["stock_code"])
    watchlist_codes = {item["stock_code"] for item in watchlist}
    if selected_stock_code not in watchlist_codes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected stock is not in your watchlist.")

    latest_fundamentals = get_latest_fundamentals_by_code(db, {selected_stock_code}).get(selected_stock_code)
    filter_results = {item.stock_code: item for item in build_filter_results(db=db, user_id=current_user.id)}
    selected_filter = filter_results.get(selected_stock_code)

    from models.stock import StockPriceHistoryORM

    history_rows = (
        db.query(StockPriceHistoryORM)
        .filter(StockPriceHistoryORM.stock_code == selected_stock_code)
        .order_by(StockPriceHistoryORM.trade_date.asc())
        .all()
    )

    ai_explanation = None
    if selected_filter:
        ai_explanation = build_stock_ai_explanation(
            db=db,
            user_id=current_user.id,
            stock_code=selected_stock_code,
            screening_result=selected_filter,
            request_id=getattr(request.state, "request_id", None) if request else None,
        )

    return StockDashboardResponse(
        selected_stock_code=selected_stock_code,
        watchlist=[WatchlistItemResponse.model_validate(item) for item in watchlist],
        price_history=[StockPriceHistoryPoint.model_validate(row) for row in history_rows],
        fundamentals=FundamentalsSnapshot.model_validate(latest_fundamentals).model_dump() if latest_fundamentals else None,
        ai_explanation=ai_explanation,
    )


@router.post("/sync")
def sync_all_watchlist_prices(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    for item in watchlist:
        update_watchlist_sync_status(
            db,
            watchlist_item_id=item.id,
            user_id=current_user.id,
            status=SYNC_STATUS_PENDING,
            error_message="Market data sync queued.",
        )
        _queue_price_sync_job(
            db,
            watchlist_item=item,
            request_id=getattr(request.state, "request_id", None),
        )

    return {
        "message": f"Queued market data sync for {len(watchlist)} watchlist items.",
        "status": SYNC_STATUS_PENDING,
        "queued_count": len(watchlist),
    }


@router.post("/{stock_code}/sync")
def sync_single_stock_price(
    stock_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    formatted_code = StockDataService.normalize_stock_code(stock_code)
    watchlist_item = (
        db.query(WatchlistORM)
        .filter(WatchlistORM.user_id == current_user.id, WatchlistORM.stock_code == formatted_code)
        .first()
    )
    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")

    update_watchlist_sync_status(
        db,
        watchlist_item_id=watchlist_item.id,
        user_id=current_user.id,
        status=SYNC_STATUS_PENDING,
        error_message="Market data sync queued.",
    )
    job = _queue_price_sync_job(
        db,
        watchlist_item=watchlist_item,
        request_id=getattr(request.state, "request_id", None),
    )
    return {
        "message": f"Queued market data sync for {formatted_code}.",
        "price_sync_status": SYNC_STATUS_PENDING,
        "job_id": job.id,
    }


@router.get("/filter", response_model=list[StockFundamentalsFilterResult])
def filter_watchlist_stocks(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return build_filter_results(db=db, user_id=current_user.id)


@router.get("/filter-metadata", response_model=FilterMetadataResponse)
def get_filter_metadata():
    return build_filter_metadata()


@router.post("/filter", response_model=StockFilterResult)
def filter_single_stock(payload: StockFilterRequest):
    return evaluate_stock(
        stock_code=payload.stock_code,
        net_income=payload.net_income,
        free_cash_flow=payload.free_cash_flow,
        revenue_growth=payload.revenue_growth,
    )
