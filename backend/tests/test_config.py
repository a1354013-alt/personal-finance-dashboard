from __future__ import annotations

from config import DEFAULT_CORS_ORIGINS, get_cors_origins


def test_default_cors_origins_include_localhost_and_loopback(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert DEFAULT_CORS_ORIGINS == "http://localhost:5173,http://127.0.0.1:5173"
    assert get_cors_origins() == ["http://localhost:5173", "http://127.0.0.1:5173"]
