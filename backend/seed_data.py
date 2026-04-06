"""
測試資料填充腳本 (v0.5.1)
執行方式：
    cd backend
    python seed_data.py
"""
import sys
import os
from datetime import date
sys.path.insert(0, os.path.dirname(__file__))

from db.database import SessionLocal, engine, Base
from models.user import UserORM
from models.expense import ExpenseORM
from models.stock import WatchlistORM, StockPriceORM
from services.auth import get_password_hash

# 確保資料表存在
Base.metadata.create_all(bind=engine)

MOCK_EXPENSES = [
    {"amount": 50000.0, "category": "薪資",     "type": "income",  "date": date(2026, 1, 5), "note": "一月薪資"},
    {"amount": 8000.0,  "category": "餐飲",     "type": "expense", "date": date(2026, 1, 10), "note": "一月餐費"},
    {"amount": 3500.0,  "category": "交通",     "type": "expense", "date": date(2026, 1, 15), "note": "捷運月票"},
    {"amount": 12000.0, "category": "房租",     "type": "expense", "date": date(2026, 1, 1), "note": "一月房租"},
    {"amount": 2000.0,  "category": "娛樂",     "type": "expense", "date": date(2026, 1, 20), "note": "電影與遊戲"},
    {"amount": 50000.0, "category": "薪資",     "type": "income",  "date": date(2026, 2, 5), "note": "二月薪資"},
    {"amount": 5000.0,  "category": "獎金",     "type": "income",  "date": date(2026, 2, 10), "note": "年終獎金"},
    {"amount": 9500.0,  "category": "餐飲",     "type": "expense", "date": date(2026, 2, 12), "note": "二月餐費"},
    {"amount": 3500.0,  "category": "交通",     "type": "expense", "date": date(2026, 2, 1), "note": "捷運月票"},
    {"amount": 12000.0, "category": "房租",     "type": "expense", "date": date(2026, 2, 1), "note": "二月房租"},
    {"amount": 4500.0,  "category": "購物",     "type": "expense", "date": date(2026, 2, 14), "note": "情人節禮物"},
    {"amount": 50000.0, "category": "薪資",     "type": "income",  "date": date(2026, 3, 5), "note": "三月薪資"},
    {"amount": 7800.0,  "category": "餐飲",     "type": "expense", "date": date(2026, 3, 10), "note": "三月餐費"},
    {"amount": 3500.0,  "category": "交通",     "type": "expense", "date": date(2026, 3, 1), "note": "捷運月票"},
    {"amount": 12000.0, "category": "房租",     "type": "expense", "date": date(2026, 3, 1), "note": "三月房租"},
    {"amount": 15000.0, "category": "醫療",     "type": "expense", "date": date(2026, 3, 8), "note": "健康檢查"},
    {"amount": 3000.0,  "category": "投資收益", "type": "income",  "date": date(2026, 3, 15), "note": "股息收入"},
]

MOCK_WATCHLIST = [
    {"stock_code": "2330.TW", "name": "台積電"},
    {"stock_code": "2317.TW", "name": "鴻海"},
    {"stock_code": "2454.TW", "name": "聯發科"},
    {"stock_code": "2382.TW", "name": "廣達"},
    {"stock_code": "AAPL",    "name": "Apple"},
    {"stock_code": "NVDA",    "name": "NVIDIA"},
]

MOCK_PRICES = [
    {"stock_code": "2330.TW", "trade_date": "2026-03-15", "close": 850.0,  "open": 845.0,  "high": 855.0,  "low": 840.0,  "volume": 25000.0},
    {"stock_code": "2317.TW", "trade_date": "2026-03-15", "close": 168.5,  "open": 165.0,  "high": 170.0,  "low": 164.0,  "volume": 45000.0},
    {"stock_code": "2454.TW", "trade_date": "2026-03-15", "close": 1120.0, "open": 1100.0, "high": 1130.0, "low": 1090.0, "volume": 1200.0},
    {"stock_code": "2382.TW", "trade_date": "2026-03-15", "close": 285.0,  "open": 280.0,  "high": 288.0,  "low": 278.0,  "volume": 8000.0},
    {"stock_code": "AAPL",    "trade_date": "2026-03-15", "close": 172.3,  "open": 170.0,  "high": 175.0,  "low": 169.0,  "volume": 55000000.0},
    {"stock_code": "NVDA",    "trade_date": "2026-03-15", "close": 875.4,  "open": 860.0,  "high": 885.0,  "low": 855.0,  "volume": 42000000.0},
]

def seed():
    db = SessionLocal()
    try:
        # 建立 Demo User
        demo_email = "demo@example.com"
        demo_user = db.query(UserORM).filter(UserORM.email == demo_email).first()
        if not demo_user:
            print(f"建立 Demo User: {demo_email}")
            demo_user = UserORM(
                email=demo_email,
                password_hash=get_password_hash("demo1234")
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

        # 清空舊資料 (只清空該 Demo User 的隔離資料，價格資料是共享的)
        db.query(ExpenseORM).filter(ExpenseORM.user_id == demo_user.id).delete()
        db.query(WatchlistORM).filter(WatchlistORM.user_id == demo_user.id).delete()
        db.commit()

        # 填入記帳資料
        for item in MOCK_EXPENSES:
            db.add(ExpenseORM(user_id=demo_user.id, **item))

        # 填入自選股資料
        for item in MOCK_WATCHLIST:
            db.add(WatchlistORM(user_id=demo_user.id, **item))

        # 填入價格資料 (共享資料)
        for item in MOCK_PRICES:
            # 檢查是否已存在相同代碼與日期的資料
            existing = db.query(StockPriceORM).filter(
                StockPriceORM.stock_code == item["stock_code"],
                StockPriceORM.trade_date == item["trade_date"]
            ).first()
            if not existing:
                db.add(StockPriceORM(**item))

        db.commit()
        print(f"✅ 已為 {demo_email} 填入 {len(MOCK_EXPENSES)} 筆記帳資料、{len(MOCK_WATCHLIST)} 筆自選股資料")
        print(f"✅ 已更新市場共享價格資料 {len(MOCK_PRICES)} 筆")
        print(f"Demo 帳號: {demo_email}")
        print(f"Demo 密碼: demo1234")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
