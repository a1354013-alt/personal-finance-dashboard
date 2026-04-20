from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.fundamentals import FundamentalsSnapshot, FundamentalsSyncOptions
from models.stock import (
    StockFilterRequest,
    StockFilterResult,
    WatchlistCreate,
    WatchlistItemResponse,
    WatchlistORM,
)
from models.stocks_filter import FilterMetadataResponse, StockFundamentalsFilterResult
from models.user import UserORM
from providers.fundamentals import get_fundamentals_provider
from services.auth import get_current_user
from services.fundamentals_service import sync_fundamentals
from services.stock_data_service import StockDataService
from services.stock_filter import evaluate_stock
from services.stocks_fundamentals_screening_service import build_filter_metadata, build_filter_results
from services.watchlist_service import (
    SYNC_STATUS_SUCCESS,
    build_watchlist_item,
    create_watchlist_item,
    delete_watchlist_item,
    list_watchlist,
    sync_stock_price,
    sync_watchlist_item_background,
)

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])


@router.get("/watchlist", response_model=list[WatchlistItemResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return list_watchlist(db, user_id=current_user.id)


@router.post("/watchlist", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    request: WatchlistCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    try:
        new_item = create_watchlist_item(db, user_id=current_user.id, stock_code=request.stock_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # Price/name sync is intentionally decoupled from creation semantics.
    background_tasks.add_task(sync_watchlist_item_background, watchlist_item_id=new_item.id)
    return build_watchlist_item(db, item=new_item)


@router.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_from_watchlist(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    ok = delete_watchlist_item(db, user_id=current_user.id, item_id=item_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")


@router.post("/fundamentals/sync", response_model=list[FundamentalsSnapshot])
def sync_watchlist_fundamentals(
    payload: FundamentalsSyncOptions,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    # IMPORTANT: this route must be defined before `/{stock_code}/sync` to avoid path conflicts.
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    provider = get_fundamentals_provider()
    rows = [
        sync_fundamentals(db, stock_code=item.stock_code, provider=provider, force=payload.force) for item in watchlist
    ]
    return [FundamentalsSnapshot.model_validate(row) for row in rows]


@router.post("/fundamentals/{stock_code}/sync", response_model=FundamentalsSnapshot)
def sync_single_fundamentals(
    stock_code: str,
    payload: FundamentalsSyncOptions,
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Stock is not in your watchlist.")

    provider = get_fundamentals_provider()
    row = sync_fundamentals(db, stock_code=formatted_code, provider=provider, force=payload.force)
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


@router.post("/sync")
def sync_all_watchlist_prices(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    success_count = 0
    failed_codes: list[str] = []

    for item in watchlist:
        if sync_stock_price(db, stock_code=item.stock_code, watchlist_item=item):
            success_count += 1
        else:
            failed_codes.append(item.stock_code)

    return {
        "message": f"Synchronized {success_count} of {len(watchlist)} watchlist items.",
        "success_count": success_count,
        "failed_codes": failed_codes,
    }


@router.post("/{stock_code}/sync")
def sync_single_stock_price(
    stock_code: str,
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Stock is not in your watchlist.")

    if sync_stock_price(db, stock_code=formatted_code, watchlist_item=watchlist_item):
        return {"message": f"Synchronized {formatted_code} successfully.", "price_sync_status": SYNC_STATUS_SUCCESS}

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Unable to fetch the latest price for {formatted_code}.",
    )


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
