"""
FastAPI 主程式 (v0.6.0)
配置 API 路由、中介軟體與資料庫初始化。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import engine, Base
from routers import expenses, stocks, dashboard, ai, auth, budgets

# 初始化資料庫
# 匯入所有 ORM 模型，確保 Base.metadata 包含所有 table
from models.user import UserORM
from models.expense import ExpenseORM
from models.stock import WatchlistORM, StockPriceORM
from models.budget import BudgetORM

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Personal Finance Dashboard API",
    description="提供記帳、股票篩選與 AI 財務摘要功能的後端服務 (含 JWT 認證與真實股票資料)",
    version="0.6.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(stocks.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(budgets.router)

@app.get("/")
def read_root():
    return {
        "message": "Personal Finance Dashboard API is running",
        "docs": "/docs",
        "version": "0.6.0"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
