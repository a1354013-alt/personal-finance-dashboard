from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.jobs.job_runner import JOB_TYPE_SYNC_STOCK_MARKET_DATA
from db.database import get_db
from models.fundamentals import FundamentalsSnapshot, FundamentalsSyncOptions
from models.job import CreateJobRequest
from models.stock import (
    StockAIAnalysisResponse,
    StockDashboardResponse,
    StockFilterRequest,
    StockFilterResult,
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
from services.stock_ai_analysis_service import build_stock_ai_analysis
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
