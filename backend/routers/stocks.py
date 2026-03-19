"""
股票模組路由
  - /api/stocks/watchlist  自選股清單
  - /api/stocks/filter     股票篩選引擎
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from models.stock import WatchlistORM, WatchlistItemResponse, StockFilterRequest, StockFilterResult
from services.stock_filter import evaluate_stock

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])


@router.get("/watchlist", response_model=List[WatchlistItemResponse])
def get_watchlist(db: Session = Depends(get_db)):
    """
    點 3: 取得自選股清單 (完全移除 seed_watchlist 呼叫，確保 GET 不產生資料庫寫入行為)
    """
    return db.query(WatchlistORM).all()


# ── Mock 股票基本面資料 ──────────────────────────────────────────────────────

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
    對所有 mock 股票執行篩選引擎。
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
