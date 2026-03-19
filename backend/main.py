"""
Personal Finance Dashboard - FastAPI 後端主程式

啟動方式：
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

API 文件：http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import engine, Base
from routers import expenses, stocks, dashboard, ai

# ── 建立資料表（若不存在）────────────────────────────────────────────────────
# 匯入所有 ORM 模型，確保 Base.metadata 包含所有 table
from models.expense import ExpenseORM  # noqa: F401
from models.stock import WatchlistORM  # noqa: F401

Base.metadata.create_all(bind=engine)

# ── FastAPI 應用程式 ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Personal Finance Dashboard API",
    description="記帳系統、股票模組、股票篩選引擎、AI 摘要",
    version="1.0.0",
)

# ── CORS 設定（允許前端 localhost:5173 跨域）────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由掛載 ─────────────────────────────────────────────────────────────────
app.include_router(expenses.router)
app.include_router(stocks.router)
app.include_router(dashboard.router)
app.include_router(ai.router)


@app.get("/")
def root():
    return {
        "message": "Personal Finance Dashboard API is running",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
