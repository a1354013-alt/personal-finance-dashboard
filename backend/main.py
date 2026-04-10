from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_VERSION, get_cors_origins
from db.database import init_db
from routers import ai, auth, budgets, dashboard, expenses, stocks
from services.auth import validate_secret_key_configuration

validate_secret_key_configuration()
init_db()

app = FastAPI(
    title="Personal Finance Dashboard API",
    description="API for the Personal Finance Dashboard demo project.",
    version=APP_VERSION,
)

cors_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(stocks.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(budgets.router)


@app.get("/")
def read_root():
    return {
        "message": "Personal Finance Dashboard API is running.",
        "docs": "/docs",
        "version": APP_VERSION,
        "cors_origins": cors_origins,
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "version": APP_VERSION}
