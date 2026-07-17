from __future__ import annotations

import pytest

import config
from config import DEFAULT_CORS_ORIGINS, get_cors_origins, validate_python_runtime


def test_default_cors_origins_include_localhost_and_loopback(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert DEFAULT_CORS_ORIGINS == "http://localhost:5173,http://127.0.0.1:5173"
    assert get_cors_origins() == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_validate_python_runtime_accepts_supported_versions(monkeypatch):
    monkeypatch.setattr(config.sys, "version_info", (3, 11, 9))
    validate_python_runtime()
    monkeypatch.setattr(config.sys, "version_info", (3, 12, 4))
    validate_python_runtime()


def test_validate_python_runtime_rejects_unsupported_versions(monkeypatch):
    monkeypatch.setattr(config.sys, "version_info", (3, 13, 0))
    with pytest.raises(RuntimeError, match="Unsupported Python 3.13"):
        validate_python_runtime()
