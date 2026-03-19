"""
股票模組路由
  - /api/stocks/watchlist  自選股清單（含 mock 股價）
  - /api/stocks/filter     股票篩選引擎
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from models.stock import WatchlistORM, WatchlistItemResponse, StockFilterRequest, StockFilterResult
from services.stock_filter import evaluate_stock

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])


# ── Mock 自選股資料（初始化時寫入 DB）────────────────────────────────────────

MOCK_WATCHLIST = [
    {"stock_code": "2330", "name": "台積電",   "price": 850.0,  "date": "2024-03-15"},
    {"stock_code": "2317", "name": "鴻海",     "price": 168.5,  "date": "2024-03-15"},
    {"stock_code": "2454", "name": "聯發科",   "price": 1120.0, "date": "2024-03-15"},
    {"stock_code": "2382", "name": "廣達",     "price": 285.0,  "date": "2024-03-15"},
    {"stock_code": "AAPL", "name": "Apple",    "price": 172.3,  "date": "2024-03-15"},
    {"stock_code": "NVDA", "name": "NVIDIA",   "price": 875.4,  "date": "2024-03-15"},
]


def seed_watchlist(db: Session):
    """若 watchlist 為空則填入 mock 資料"""
    if db.query(WatchlistORM).count() == 0:
        for item in MOCK_WATCHLIST:
            db.add(WatchlistORM(**item))
        db.commit()


@router.get("/watchlist", response_model=List[WatchlistItemResponse])
def get_watchlist(db: Session = Depends(get_db)):
    """取得自選股清單（含 mock 股價）"""
    seed_watchlist(db)
    return db.query(WatchlistORM).all()


# ── Mock 股票基本面資料（用於篩選引擎示範）──────────────────────────────────

MOCK_FUNDAMENTALS = [
    {"stock_code": "2330", "net_income": 500_000, "free_cash_flow": 300_000, "revenue_growth": 12.5},
    {"stock_code": "2317", "net_income": 80_000,  "free_cash_flow": -5_000,  "revenue_growth": 3.2},
    {"stock_code": "2454", "net_income": 120_000, "free_cash_flow": 90_000,  "revenue_growth": -2.1},
    {"stock_code": "2382", "net_income": 45_000,  "free_cash_flow": 30_000,  "revenue_growth": 8.7},
    {"stock_code": "AAPL", "net_income": 970_000, "free_cash_flow": 850_000, "revenue_growth": 5.0},
    {"stock_code": "NVDA", "net_income": 430_000, "free_cash_flow": 380_000, "revenue_growth": 122.0},
]


@router.get("/filter", response_model=List[StockFilterResult])
def filter_stocks():
    """
    對所有 mock 股票執行篩選引擎，回傳每支股票的通過狀態與失敗原因。
    前端可依 passed 欄位分類顯示。
    """
    results = []
    for stock in MOCK_FUNDAMENTALS:
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
