"""
股票模組路由 - /api/stocks (v0.5.1)
提供使用者自選股清單、真實價格同步與股票篩選功能。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.stock import (
    WatchlistORM, StockPriceORM, 
    WatchlistCreate, WatchlistItemResponse,
    StockFilterRequest, StockFilterResult
)
from models.user import UserORM
from services.auth import get_current_user
from services.stock_data_service import StockDataService
from services.stock_filter import evaluate_stock

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])


@router.get("/watchlist", response_model=List[WatchlistItemResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """取得當前使用者的自選股清單"""
    items = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    
    results = []
    for item in items:
        # 取得該股票最新的價格記錄 (價格歷史為市場共享資料)
        latest_price = db.query(StockPriceORM).filter(
            StockPriceORM.stock_code == item.stock_code
        ).order_by(StockPriceORM.trade_date.desc()).first()
        
        results.append({
            "id": item.id,
            "user_id": item.user_id,
            "stock_code": item.stock_code,
            "name": item.name,
            "price": latest_price.close if latest_price else None,
            "date": latest_price.trade_date if latest_price else None,
            "volume": latest_price.volume if latest_price else None,
            "price_sync_status": "success" if latest_price else "pending"
        })
    
    return results


@router.post("/watchlist", response_model=WatchlistItemResponse)
def add_to_watchlist(
    request: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """新增自選股"""
    # 使用服務端的格式化邏輯 (點 3)
    stock_code = StockDataService._format_stock_code(request.stock_code)
    
    # 檢查是否已存在 (去重邏輯)
    existing = db.query(WatchlistORM).filter(
        WatchlistORM.user_id == current_user.id,
        WatchlistORM.stock_code == stock_code
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="此股票已在自選股清單中")
    
    new_item = WatchlistORM(
        user_id=current_user.id,
        stock_code=stock_code
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    # 嘗試同步一次最新價格 (點 6)
    # 若同步失敗，仍回傳成功新增但標示同步狀態
    sync_success = _sync_stock_price_internal(stock_code, db)
    
    return {
        "id": new_item.id,
        "user_id": new_item.user_id,
        "stock_code": new_item.stock_code,
        "name": new_item.name,
        "price_sync_status": "success" if sync_success else "failed"
    }


@router.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_from_watchlist(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """刪除自選股"""
    item = db.query(WatchlistORM).filter(
        WatchlistORM.id == item_id,
        WatchlistORM.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="找不到該自選股記錄")
    
    db.delete(item)
    db.commit()
    return None


@router.post("/sync", status_code=status.HTTP_200_OK)
def sync_all_watchlist_prices(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """手動同步所有自選股的最新價格"""
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    codes = [item.stock_code for item in watchlist]
    
    success_count = 0
    for code in codes:
        if _sync_stock_price_internal(code, db):
            success_count += 1
            
    return {"message": f"同步完成，成功更新 {success_count} 檔股票價格"}


@router.post("/{stock_code}/sync", status_code=status.HTTP_200_OK)
def sync_single_stock_price(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """手動同步單一股票價格 (點 5)"""
    formatted_code = StockDataService._format_stock_code(stock_code)
    
    # 權限驗證：必須在該使用者的自選股清單中
    in_watchlist = db.query(WatchlistORM).filter(
        WatchlistORM.user_id == current_user.id,
        WatchlistORM.stock_code == formatted_code
    ).first()
    
    if not in_watchlist:
        raise HTTPException(status_code=403, detail="您無權同步此股票，請先將其加入自選股")

    if _sync_stock_price_internal(formatted_code, db):
        return {"message": f"股票 {formatted_code} 同步成功"}
    else:
        raise HTTPException(status_code=500, detail=f"股票 {formatted_code} 同步失敗")


def _sync_stock_price_internal(stock_code: str, db: Session) -> bool:
    """內部輔助函式：同步股票價格到資料庫"""
    price_data = StockDataService.fetch_real_price(stock_code)
    
    if not price_data:
        return False
        
    # 檢查該日期是否已存在 (市場價格資料共享)
    existing = db.query(StockPriceORM).filter(
        StockPriceORM.stock_code == stock_code,
        StockPriceORM.trade_date == price_data["trade_date"]
    ).first()
    
    if existing:
        # 更新現有記錄
        existing.open = price_data["open"]
        existing.high = price_data["high"]
        existing.low = price_data["low"]
        existing.close = price_data["close"]
        existing.volume = price_data["volume"]
    else:
        # 新增記錄
        new_price = StockPriceORM(**price_data)
        db.add(new_price)
    
    db.commit()
    return True


# ── 既有功能：Mock 股票基本面篩選 ───────────────────────────────────────────

MOCK_FUNDAMENTALS = [
    {"stock_code": "2330.TW", "net_income": 500_000, "free_cash_flow": 300_000, "revenue_growth": 12.5},
    {"stock_code": "2317.TW", "net_income": 80_000,  "free_cash_flow": -5_000,  "revenue_growth": 3.2},
    {"stock_code": "2454.TW", "net_income": 120_000, "free_cash_flow": 90_000,  "revenue_growth": -2.1},
    {"stock_code": "2382.TW", "net_income": 45_000,  "free_cash_flow": 30_000,  "revenue_growth": 8.7},
    {"stock_code": "AAPL", "net_income": 970_000, "free_cash_flow": 850_000, "revenue_growth": 5.0},
    {"stock_code": "NVDA", "net_income": 430_000, "free_cash_flow": 380_000, "revenue_growth": 122.0},
]


@router.get("/filter", response_model=List[StockFilterResult])
def filter_watchlist_stocks(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """
    對當前使用者的自選股執行篩選引擎。
    此功能仍依賴 Mock Fundamentals。
    """
    watchlist = db.query(WatchlistORM).filter(WatchlistORM.user_id == current_user.id).all()
    watchlist_codes = {s.stock_code for s in watchlist}
    
    results = []
    for stock in MOCK_FUNDAMENTALS:
        if stock["stock_code"] in watchlist_codes:
            result = evaluate_stock(
                stock_code=stock["stock_code"],
                net_income=stock["net_income"],
                free_cash_flow=stock["free_cash_flow"],
                revenue_growth=stock["revenue_growth"],
            )
            results.append(result)
    return results


@router.post("/filter", response_model=StockFilterResult)
def filter_single_stock(payload: StockFilterRequest):
    """對單一股票自訂基本面數據進行篩選"""
    return evaluate_stock(
        stock_code=payload.stock_code,
        net_income=payload.net_income,
        free_cash_flow=payload.free_cash_flow,
        revenue_growth=payload.revenue_growth,
    )
