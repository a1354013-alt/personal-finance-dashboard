from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DEFAULT_DATABASE_URL = "sqlite:///./finance.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

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

    relative_path = database_url.replace("sqlite:///", "", 1)
    return Path(relative_path).resolve()


def database_exists(database_url: str = DATABASE_URL) -> bool:
    sqlite_path = resolve_sqlite_path(database_url)
    if sqlite_path is None:
        return True
    return sqlite_path.exists()


def init_db() -> None:
    from models.budget import BudgetORM  # noqa: F401
    from models.expense import ExpenseORM  # noqa: F401
    from models.stock import StockPriceORM, WatchlistORM  # noqa: F401
    from models.user import UserORM  # noqa: F401

    sqlite_path = resolve_sqlite_path()
    if sqlite_path is not None and sqlite_path.exists():
        return

    Base.metadata.create_all(bind=engine)


def reset_sqlite_db(database_url: str = DATABASE_URL) -> Path:
    sqlite_path = resolve_sqlite_path(database_url)
    if sqlite_path is None:
        raise RuntimeError("Reset is only supported for SQLite databases.")

    engine.dispose()
    if sqlite_path.exists():
        sqlite_path.unlink()

    Base.metadata.create_all(bind=engine)
    return sqlite_path
