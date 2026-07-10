from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.jobs import get_job_runner
from config import APP_VERSION, DEFAULT_RATE_LIMIT_PER_MINUTE, get_cors_origins
from db.database import init_db
from logging_config import bind_request_id, configure_logging, get_request_id_from_request
from routers import ai, auth, budgets, dashboard, expenses, imports, recurring_transactions, reports, stocks
from services.auth import validate_secret_key_configuration

configure_logging()
logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    def __init__(self, *, limit_per_minute: int = DEFAULT_RATE_LIMIT_PER_MINUTE) -> None:
        self._limit = limit_per_minute
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        window = self._windows[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self._limit:
            return False
        window.append(now)
        return True


rate_limiter = InMemoryRateLimiter()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_secret_key_configuration()
    init_db()
    runner = get_job_runner()
    runner.start()
    yield
    runner.stop()


app = FastAPI(
    title="Personal Finance Dashboard API",
    description="API for the Personal Finance Dashboard demo project.",
    version=APP_VERSION,
    lifespan=lifespan,
)

cors_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def observability_and_rate_limit_middleware(request: Request, call_next):
    request_id = get_request_id_from_request(request)
    bind_request_id(request_id)
    request.state.request_id = request_id
    started_at = time.perf_counter()

    client_host = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(client_host):
        logger.warning(
            "rate limit exceeded",
            extra={"request_id": request_id, "path": request.url.path, "method": request.method, "status_code": 429},
        )
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please retry later."})

    try:
        response = await call_next(request)
    except Exception as exc:
        execution_time_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.error(
            "request failed",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": 500,
                "execution_time_ms": execution_time_ms,
            },
            exc_info=exc,
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error.", "request_id": request_id})

    execution_time_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Execution-Time-Ms"] = str(execution_time_ms)
    logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "execution_time_ms": execution_time_ms,
        },
    )
    return response


app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(imports.router)
app.include_router(recurring_transactions.router)
app.include_router(stocks.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(budgets.router)
app.include_router(reports.router)


@app.get("/")
def read_root():
    return {
        "message": "Personal Finance Dashboard API is running.",
        "docs": "/docs",
        "version": APP_VERSION,
        "cors_origins": cors_origins,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "version": APP_VERSION}
