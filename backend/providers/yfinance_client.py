from __future__ import annotations


def get_yfinance():
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - exercised by import smoke and targeted tests
        raise RuntimeError(
            "yfinance is required for live market data and fundamentals sync. "
            "Install backend requirements first with `pip install -r backend/requirements.txt`."
        ) from exc

    return yf
