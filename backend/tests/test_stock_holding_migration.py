from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]


def run_alembic(database_path: Path, *args: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    env["SECRET_KEY"] = "migration-test-secret"
    env["ENV"] = "development"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def execute_sql(database_path: Path, statement: str, params: tuple = ()) -> None:
    with sqlite3.connect(database_path) as conn:
        conn.execute(statement, params)
        conn.commit()


def fetch_holdings(database_path: Path) -> list[tuple]:
    with sqlite3.connect(database_path) as conn:
        return conn.execute(
            "SELECT id, stock_code, shares, average_cost, currency, note FROM stock_holdings ORDER BY id"
        ).fetchall()


def fetch_trades(database_path: Path) -> list[tuple]:
    with sqlite3.connect(database_path) as conn:
        return conn.execute(
            """
            SELECT user_id, stock_code, trade_type, trade_date, shares, price, currency, note, source_holding_id
            FROM stock_trades
            ORDER BY user_id, stock_code, trade_date, id
            """
        ).fetchall()


def test_0010_merges_duplicate_holdings_and_enforces_unique_constraint(tmp_path):
    database_path = tmp_path / "migration.db"
    run_alembic(database_path, "upgrade", "0009_add_stock_holdings")

    execute_sql(
        database_path,
        "INSERT INTO users (id, email, password_hash, created_at) VALUES (1, 'migration@example.com', 'hash', '2026-07-13 00:00:00')",
    )
    execute_sql(
        database_path,
        """
        INSERT INTO stock_holdings
          (id, user_id, stock_code, shares, average_cost, currency, note, created_at, updated_at)
        VALUES
          (1, 1, 'AAPL', '2.000000', '150.0000', 'USD', 'oldest note', '2026-07-13 00:00:00', '2026-07-13 00:00:00')
        """,
    )
    execute_sql(
        database_path,
        """
        INSERT INTO stock_holdings
          (id, user_id, stock_code, shares, average_cost, currency, note, created_at, updated_at)
        VALUES
          (2, 1, 'AAPL', '3.000000', '200.0000', 'USD', 'newer note', '2026-07-13 00:01:00', '2026-07-13 00:01:00')
        """,
    )

    run_alembic(database_path, "upgrade", "0010_enforce_unique_stock_holdings")

    rows = fetch_holdings(database_path)
    assert len(rows) == 1
    row = rows[0]
    assert row[0] == 1
    assert row[1] == "AAPL"
    assert Decimal(str(row[2])) == Decimal("5")
    assert Decimal(str(row[3])).quantize(Decimal("0.0001")) == Decimal("180.0000")
    assert row[4] == "USD"
    assert row[5] == "oldest note"

    with pytest.raises(sqlite3.IntegrityError):
        execute_sql(
            database_path,
            """
            INSERT INTO stock_holdings
              (user_id, stock_code, shares, average_cost, currency, note, created_at, updated_at)
            VALUES
              (1, 'AAPL', '1.000000', '190.0000', 'USD', 'duplicate', '2026-07-13 00:02:00', '2026-07-13 00:02:00')
            """,
        )

    run_alembic(database_path, "downgrade", "0009_add_stock_holdings")
    run_alembic(database_path, "upgrade", "0010_enforce_unique_stock_holdings")
    assert len(fetch_holdings(database_path)) == 1


def test_0011_backfills_opening_balance_trades_and_survives_reupgrade(tmp_path):
    database_path = tmp_path / "migration-0011.db"
    run_alembic(database_path, "upgrade", "0010_enforce_unique_stock_holdings")

    execute_sql(
        database_path,
        "INSERT INTO users (id, email, password_hash, created_at) VALUES (1, 'a@example.com', 'hash', '2026-07-13 00:00:00')",
    )
    execute_sql(
        database_path,
        "INSERT INTO users (id, email, password_hash, created_at) VALUES (2, 'b@example.com', 'hash', '2026-07-13 00:00:00')",
    )
    execute_sql(
        database_path,
        """
        INSERT INTO stock_holdings
          (id, user_id, stock_code, shares, average_cost, currency, note, created_at, updated_at)
        VALUES
          (11, 1, '2330.TW', '5.000000', '800.0000', 'TWD', 'core tw', '2026-07-13 00:00:00', '2026-07-13 00:00:00'),
          (12, 1, 'AAPL', '2.000000', '150.0000', 'USD', 'core us', '2026-07-13 00:05:00', '2026-07-13 00:05:00'),
          (13, 2, 'AAPL', '7.000000', '120.0000', 'USD', 'other user', '2026-07-13 00:10:00', '2026-07-13 00:10:00')
        """,
    )

    run_alembic(database_path, "upgrade", "0011_add_stock_trade_ledger")

    trades = fetch_trades(database_path)
    assert trades == [
        (1, "2330.TW", "OPENING_BALANCE", "2026-07-13", 5, 800, "TWD", "core tw", 11),
        (1, "AAPL", "OPENING_BALANCE", "2026-07-13", 2, 150, "USD", "core us", 12),
        (2, "AAPL", "OPENING_BALANCE", "2026-07-13", 7, 120, "USD", "other user", 13),
    ]

    run_alembic(database_path, "downgrade", "0010_enforce_unique_stock_holdings")
    with sqlite3.connect(database_path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "stock_trades" not in tables
    assert len(fetch_holdings(database_path)) == 3

    run_alembic(database_path, "upgrade", "0011_add_stock_trade_ledger")
    trades = fetch_trades(database_path)
    assert len(trades) == 3
    assert [row[8] for row in trades] == [11, 12, 13]


def test_0011_handles_empty_holdings_table(tmp_path):
    database_path = tmp_path / "migration-0011-empty.db"
    run_alembic(database_path, "upgrade", "0011_add_stock_trade_ledger")
    assert fetch_trades(database_path) == []
