from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from db.database import BACKEND_DIR, normalize_database_url


def upgrade_head(database_url: str) -> None:
    """Run Alembic migrations up to head for the given database_url."""

    config_path = (BACKEND_DIR / "alembic.ini").resolve()
    if not config_path.exists():
        raise RuntimeError(f"Alembic config not found: {config_path}")

    alembic_cfg = Config(str(config_path))
    alembic_cfg.set_main_option("script_location", str((BACKEND_DIR / "alembic").resolve()))
    alembic_cfg.set_main_option("sqlalchemy.url", normalize_database_url(database_url))
    command.upgrade(alembic_cfg, "head")

