"""
資料填充腳本 - 生成 mock 記帳資料
執行方式：
    cd backend
    python seed_data.py
"""
import sys
import os
from datetime import date  # 點 1: 匯入 date
sys.path.insert(0, os.path.dirname(__file__))

from db.database import SessionLocal, engine, Base
from models.expense import ExpenseORM
from models.stock import WatchlistORM

# 確保資料表存在
Base.metadata.create_all(bind=engine)

MOCK_EXPENSES = [
    {"amount": 50000.0, "category": "薪資",     "type": "income",  "date": date(2024, 1, 5), "note": "一月薪資"},
    {"amount": 8000.0,  "category": "餐飲",     "type": "expense", "date": date(2024, 1, 10), "note": "一月餐費"},
    {"amount": 3500.0,  "category": "交通",     "type": "expense", "date": date(2024, 1, 15), "note": "捷運月票"},
    {"amount": 12000.0, "category": "房租",     "type": "expense", "date": date(2024, 1, 1), "note": "一月房租"},
    {"amount": 2000.0,  "category": "娛樂",     "type": "expense", "date": date(2024, 1, 20), "note": "電影與遊戲"},
    {"amount": 50000.0, "category": "薪資",     "type": "income",  "date": date(2024, 2, 5), "note": "二月薪資"},
    {"amount": 5000.0,  "category": "獎金",     "type": "income",  "date": date(2024, 2, 10), "note": "年終獎金"},
    {"amount": 9500.0,  "category": "餐飲",     "type": "expense", "date": date(2024, 2, 12), "note": "二月餐費"},
    {"amount": 3500.0,  "category": "交通",     "type": "expense", "date": date(2024, 2, 1), "note": "捷運月票"},
    {"amount": 12000.0, "category": "房租",     "type": "expense", "date": date(2024, 2, 1), "note": "二月房租"},
    {"amount": 4500.0,  "category": "購物",     "type": "expense", "date": date(2024, 2, 14), "note": "情人節禮物"},
    {"amount": 50000.0, "category": "薪資",     "type": "income",  "date": date(2024, 3, 5), "note": "三月薪資"},
    {"amount": 7800.0,  "category": "餐飲",     "type": "expense", "date": date(2024, 3, 10), "note": "三月餐費"},
    {"amount": 3500.0,  "category": "交通",     "type": "expense", "date": date(2024, 3, 1), "note": "捷運月票"},
    {"amount": 12000.0, "category": "房租",     "type": "expense", "date": date(2024, 3, 1), "note": "三月房租"},
    {"amount": 15000.0, "category": "醫療",     "type": "expense", "date": date(2024, 3, 8), "note": "健康檢查"},
    {"amount": 3000.0,  "category": "投資收益", "type": "income",  "date": date(2024, 3, 15), "note": "股息收入"},
]

MOCK_WATCHLIST = [
    {"stock_code": "2330", "name": "台積電",   "price": 850.0,  "date": "2024-03-15"},
    {"stock_code": "2317", "name": "鴻海",     "price": 168.5,  "date": "2024-03-15"},
    {"stock_code": "2454", "name": "聯發科",   "price": 1120.0, "date": "2024-03-15"},
    {"stock_code": "2382", "name": "廣達",     "price": 285.0,  "date": "2024-03-15"},
    {"stock_code": "AAPL", "name": "Apple",    "price": 172.3,  "date": "2024-03-15"},
    {"stock_code": "NVDA", "name": "NVIDIA",   "price": 875.4,  "date": "2024-03-15"},
]


def seed():
    db = SessionLocal()
    try:
        # 清空舊資料
        db.query(ExpenseORM).delete()
        db.query(WatchlistORM).delete()
        db.commit()

        # 填入記帳資料
        for item in MOCK_EXPENSES:
            db.add(ExpenseORM(**item))

        # 填入自選股資料
        for item in MOCK_WATCHLIST:
            db.add(WatchlistORM(**item))

        db.commit()
        print(f"✅ 已填入 {len(MOCK_EXPENSES)} 筆記帳資料、{len(MOCK_WATCHLIST)} 筆自選股資料")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
