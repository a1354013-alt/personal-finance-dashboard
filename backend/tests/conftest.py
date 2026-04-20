from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENV", "development")

from db.database import engine, init_db, reset_sqlite_db  # noqa: E402
from main import app as fastapi_app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    reset_sqlite_db()
    init_db()
    yield
    reset_sqlite_db()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(fastapi_app)


def register_and_login(client: TestClient, email: str) -> str:
    register_response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert register_response.status_code == 201

    login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

