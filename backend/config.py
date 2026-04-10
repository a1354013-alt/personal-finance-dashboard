from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

APP_VERSION = "0.6.1"
DEFAULT_CORS_ORIGINS = "http://localhost:5173"
DEVELOPMENT_SECRET_KEY = "dev-only-change-me-in-production"


def get_cors_origins() -> list[str]:
    raw_value = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def get_secret_key() -> str:
    return os.getenv("SECRET_KEY") or DEVELOPMENT_SECRET_KEY


def is_development_mode() -> bool:
    return os.getenv("ENV", "development").lower() != "production"
