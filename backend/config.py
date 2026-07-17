from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

APP_VERSION = "1.6.0"
SUPPORTED_PYTHON_VERSIONS = {(3, 11), (3, 12)}
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
DEVELOPMENT_SECRET_KEY = "dev-only-change-me-in-production"
DEFAULT_RATE_LIMIT_PER_MINUTE = 100
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 14


def get_cors_origins() -> list[str]:
    raw_value = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def get_secret_key() -> str:
    return os.getenv("SECRET_KEY") or DEVELOPMENT_SECRET_KEY


def is_development_mode() -> bool:
    return os.getenv("ENV", "development").lower() != "production"


def validate_python_runtime() -> None:
    current = sys.version_info[:2]
    if current not in SUPPORTED_PYTHON_VERSIONS:
        supported = ", ".join(f"{major}.{minor}" for major, minor in sorted(SUPPORTED_PYTHON_VERSIONS))
        raise RuntimeError(
            f"Unsupported Python {current[0]}.{current[1]}. "
            f"Use Python {supported} for the Personal Finance Dashboard backend."
        )
