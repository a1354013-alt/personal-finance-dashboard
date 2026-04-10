from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = "sqlite:///./finance.db"
EXPECTED_TABLES = {"users", "expenses", "budgets", "watchlist", "stock_prices"}


def normalize_database_url(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        return database_url

    sqlite_path = database_url.replace("sqlite:///", "", 1)
    path_obj = Path(sqlite_path)
    if not path_obj.is_absolute():
        path_obj = (BACKEND_DIR / path_obj).resolve()
    return f"sqlite:///{path_obj.as_posix()}"


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
Base = declarative_base()


def _build_engine():
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    return create_engine(DATABASE_URL, connect_args=connect_args)


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def resolve_sqlite_path(database_url: str = DATABASE_URL) -> Path | None:
    if not database_url.startswith("sqlite:///"):
        return None
    return Path(database_url.replace("sqlite:///", "", 1)).resolve()


def init_db() -> None:
    from models.budget import BudgetORM  # noqa: F401
    from models.expense import ExpenseORM  # noqa: F401
    from models.stock import StockPriceORM, WatchlistORM  # noqa: F401
    from models.user import UserORM  # noqa: F401

    sqlite_path = resolve_sqlite_path()
    if sqlite_path is None or not sqlite_path.exists():
        Base.metadata.create_all(bind=engine)
        return

    existing_tables = set(inspect(engine).get_table_names())
    missing_tables = EXPECTED_TABLES - existing_tables
    if missing_tables:
        missing = ", ".join(sorted(missing_tables))
        raise RuntimeError(
            "Existing database schema is incompatible with the current application. "
            f"Missing tables: {missing}. Run `python seed_data.py --reset` to recreate it."
        )


def reset_sqlite_db(database_url: str = DATABASE_URL) -> Path:
    sqlite_path = resolve_sqlite_path(database_url)
    if sqlite_path is None:
        raise RuntimeError("Reset is only supported for SQLite databases.")

    engine.dispose()
    if sqlite_path.exists():
        sqlite_path.unlink()

    Base.metadata.create_all(bind=engine)
    return sqlite_path
