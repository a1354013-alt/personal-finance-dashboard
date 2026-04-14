from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DB_PATH = ROOT / 'test_smoke.db'
os.environ['DATABASE_URL'] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['ENV'] = 'development'

from db.database import SessionLocal, engine, init_db, reset_sqlite_db  # noqa: E402
from main import app  # noqa: E402
from models.stock import StockPriceORM, WatchlistORM  # noqa: E402
from routers import stocks as stocks_router  # noqa: E402

client = TestClient(app)


def mock_price(stock_code: str, close: float = 100.0, trade_date: str = '2026-04-10') -> dict:
    return {
        'stock_code': stock_code,
        'trade_date': trade_date,
        'open': close - 1,
        'high': close + 1,
        'low': close - 2,
        'close': close,
        'volume': 12345.0,
    }


@pytest.fixture(autouse=True)
def clean_db():
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    reset_sqlite_db()
    init_db()
    yield
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def register_and_login(email: str) -> str:
    register_response = client.post('/api/auth/register', json={'email': email, 'password': 'password123'})
    assert register_response.status_code == 201

    login_response = client.post('/api/auth/login', json={'email': email, 'password': 'password123'})
    assert login_response.status_code == 200
    return login_response.json()['access_token']


def auth_headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def test_auth_register_login_me():
    token = register_and_login('smoke@example.com')

    me_response = client.get('/api/auth/me', headers=auth_headers(token))
    assert me_response.status_code == 200
    assert me_response.json()['email'] == 'smoke@example.com'


def test_expenses_create_list_delete_with_user_isolation():
    token_a = register_and_login('user-a@example.com')
    token_b = register_and_login('user-b@example.com')

    create_response = client.post(
        '/api/expenses',
        headers=auth_headers(token_a),
        json={'amount': 123.45, 'category': 'Food', 'type': 'expense', 'date': '2026-04-10', 'note': 'Lunch'},
    )
    assert create_response.status_code == 201
    expense_id = create_response.json()['id']

    list_a = client.get('/api/expenses', headers=auth_headers(token_a))
    list_b = client.get('/api/expenses', headers=auth_headers(token_b))
    assert len(list_a.json()) == 1
    assert list_b.json() == []

    delete_other_user = client.delete(f'/api/expenses/{expense_id}', headers=auth_headers(token_b))
    assert delete_other_user.status_code == 404

    delete_response = client.delete(f'/api/expenses/{expense_id}', headers=auth_headers(token_a))
    assert delete_response.status_code == 200


def test_budgets_create_list_delete_and_dashboard_summary():
    token = register_and_login('budget@example.com')

    create_budget = client.post(
        '/api/budgets',
        headers=auth_headers(token),
        json={'category': 'Food', 'monthly_limit': 1000},
    )
    assert create_budget.status_code == 201
    budget_id = create_budget.json()['id']

    client.post(
        '/api/expenses',
        headers=auth_headers(token),
        json={'amount': 3000, 'category': 'Salary', 'type': 'income', 'date': '2026-04-01', 'note': 'Salary'},
    )
    client.post(
        '/api/expenses',
        headers=auth_headers(token),
        json={'amount': 700, 'category': 'Food', 'type': 'expense', 'date': '2026-04-05', 'note': 'Groceries'},
    )
    client.post(
        '/api/expenses',
        headers=auth_headers(token),
        json={'amount': 600, 'category': 'Food', 'type': 'expense', 'date': '2026-05-01', 'note': 'Next month'},
    )
    client.post(
        '/api/expenses',
        headers=auth_headers(token),
        json={'amount': 200, 'category': 'Food', 'type': 'income', 'date': '2026-04-06', 'note': 'Refund'},
    )

    budgets_response = client.get('/api/budgets', headers=auth_headers(token))
    assert budgets_response.status_code == 200
    budgets = budgets_response.json()
    assert budgets[0]['current_spent'] == 700
    assert budgets[0]['percent_used'] == 70

    dashboard_response = client.get('/api/dashboard/summary', headers=auth_headers(token))
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard['total_income'] == 3200
    assert dashboard['total_expense'] == 1300
    assert dashboard['over_budget'] == []
    assert dashboard['summary_scope']['totals'] == 'all_time'
    assert dashboard['summary_scope']['over_budget'] == 'current_month'

    advice_response = client.get('/api/ai/budget-advice', headers=auth_headers(token))
    assert advice_response.status_code == 200
    assert advice_response.json()['budget_status'][0]['current_spent'] == 700

    delete_budget = client.delete(f'/api/budgets/{budget_id}', headers=auth_headers(token))
    assert delete_budget.status_code == 204


def test_stocks_add_watchlist_success(monkeypatch: pytest.MonkeyPatch):
    token = register_and_login('stocks-add-success@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_stock_info', classmethod(lambda cls, code: {'shortName': code}))
    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(lambda cls, code: mock_price(code, close=321.0)))

    add_response = client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'NVDA'})
    assert add_response.status_code == 201
    payload = add_response.json()
    assert payload['stock_code'] == 'NVDA'
    assert payload['price_sync_status'] == 'success'
    assert payload['last_sync_error'] is None
    assert payload['last_sync_attempt_at'] is not None


def test_stocks_duplicate_add_returns_400(monkeypatch: pytest.MonkeyPatch):
    token = register_and_login('stocks-duplicate@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_stock_info', classmethod(lambda cls, code: {'shortName': code}))
    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(lambda cls, code: mock_price(code)))

    first = client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'AAPL'})
    assert first.status_code == 201

    duplicate = client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'AAPL'})
    assert duplicate.status_code == 400


def test_stocks_delete_watchlist_success(monkeypatch: pytest.MonkeyPatch):
    token = register_and_login('stocks-delete@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_stock_info', classmethod(lambda cls, code: {'shortName': code}))
    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(lambda cls, code: mock_price(code)))

    add_response = client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'MSFT'})
    item_id = add_response.json()['id']

    delete_response = client.delete(f'/api/stocks/watchlist/{item_id}', headers=auth_headers(token))
    assert delete_response.status_code == 204

    watchlist_response = client.get('/api/stocks/watchlist', headers=auth_headers(token))
    assert watchlist_response.status_code == 200
    assert watchlist_response.json() == []


def test_stocks_delete_other_user_item_returns_404(monkeypatch: pytest.MonkeyPatch):
    token_a = register_and_login('stocks-owner@example.com')
    token_b = register_and_login('stocks-other@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_stock_info', classmethod(lambda cls, code: {'shortName': code}))
    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(lambda cls, code: mock_price(code)))

    add_response = client.post('/api/stocks/watchlist', headers=auth_headers(token_a), json={'stock_code': 'TSLA'})
    item_id = add_response.json()['id']

    delete_other = client.delete(f'/api/stocks/watchlist/{item_id}', headers=auth_headers(token_b))
    assert delete_other.status_code == 404


def test_stocks_sync_all_success(monkeypatch: pytest.MonkeyPatch):
    token = register_and_login('stocks-sync-all-success@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_stock_info', classmethod(lambda cls, code: {'shortName': code}))
    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(lambda cls, code: mock_price(code, close=200.0)))

    client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'NVDA'})
    client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'AAPL'})

    sync_response = client.post('/api/stocks/sync', headers=auth_headers(token))
    assert sync_response.status_code == 200
    payload = sync_response.json()
    assert payload['success_count'] == 2
    assert payload['failed_codes'] == []

    watchlist = client.get('/api/stocks/watchlist', headers=auth_headers(token)).json()
    assert all(item['price_sync_status'] == 'success' for item in watchlist)
    assert all(item['last_sync_error'] is None for item in watchlist)
    assert all(item['last_sync_attempt_at'] is not None for item in watchlist)


def test_stocks_sync_all_partial_failure(monkeypatch: pytest.MonkeyPatch):
    token = register_and_login('stocks-sync-all-partial@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_stock_info', classmethod(lambda cls, code: {'shortName': code}))

    def mixed_price(_cls, code):
        if code == 'AAPL':
            return None
        return mock_price(code, close=444.0)

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(mixed_price))

    client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'NVDA'})
    client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'AAPL'})

    sync_response = client.post('/api/stocks/sync', headers=auth_headers(token))
    assert sync_response.status_code == 200
    payload = sync_response.json()
    assert payload['success_count'] == 1
    assert payload['failed_codes'] == ['AAPL']

    watchlist = client.get('/api/stocks/watchlist', headers=auth_headers(token)).json()
    by_code = {item['stock_code']: item for item in watchlist}
    assert by_code['NVDA']['price_sync_status'] == 'success'
    assert by_code['NVDA']['last_sync_error'] is None
    assert by_code['NVDA']['last_sync_attempt_at'] is not None
    assert by_code['AAPL']['price_sync_status'] == 'failed'
    assert by_code['AAPL']['last_sync_error']
    assert by_code['AAPL']['last_sync_attempt_at'] is not None


def test_stocks_single_sync_success(monkeypatch: pytest.MonkeyPatch):
    token = register_and_login('stocks-single-sync@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_stock_info', classmethod(lambda cls, code: {'shortName': code}))
    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(lambda cls, code: mock_price(code, close=111.0)))

    client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'AMD'})

    sync_response = client.post('/api/stocks/AMD/sync', headers=auth_headers(token))
    assert sync_response.status_code == 200
    assert sync_response.json()['price_sync_status'] == 'success'

    watchlist = client.get('/api/stocks/watchlist', headers=auth_headers(token)).json()
    assert watchlist[0]['price_sync_status'] == 'success'
    assert watchlist[0]['last_sync_error'] is None
    assert watchlist[0]['last_sync_attempt_at'] is not None


def test_stocks_single_sync_not_in_watchlist_returns_403(monkeypatch: pytest.MonkeyPatch):
    token = register_and_login('stocks-sync-403@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(lambda cls, code: mock_price(code)))

    sync_response = client.post('/api/stocks/NVDA/sync', headers=auth_headers(token))
    assert sync_response.status_code == 403


def test_stocks_status_persistence_failed_pending_success(monkeypatch: pytest.MonkeyPatch):
    token = register_and_login('stocks-status-persist@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_stock_info', classmethod(lambda cls, code: {'shortName': code}))
    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(lambda cls, code: mock_price(code, close=222.0)))

    add_response = client.post('/api/stocks/watchlist', headers=auth_headers(token), json={'stock_code': 'NVDA'})
    assert add_response.status_code == 201
    item_id = add_response.json()['id']

    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        item = db.query(WatchlistORM).filter(WatchlistORM.id == item_id).first()
        assert item is not None

        item.price_sync_status = 'failed'
        item.last_sync_error = 'Manual failed state for persistence test.'
        item.last_sync_attempt_at = now
        db.commit()
        failed_view = client.get('/api/stocks/watchlist', headers=auth_headers(token)).json()[0]
        assert failed_view['price_sync_status'] == 'failed'
        assert failed_view['last_sync_error'] == 'Manual failed state for persistence test.'
        assert failed_view['last_sync_attempt_at'] is not None

        item.price_sync_status = 'pending'
        item.last_sync_error = 'Waiting retry.'
        item.last_sync_attempt_at = now
        db.commit()
        pending_view = client.get('/api/stocks/watchlist', headers=auth_headers(token)).json()[0]
        assert pending_view['price_sync_status'] == 'pending'
        assert pending_view['last_sync_error'] == 'Waiting retry.'
        assert pending_view['last_sync_attempt_at'] is not None

        db.query(StockPriceORM).filter(StockPriceORM.stock_code == item.stock_code).delete(synchronize_session=False)
        item.price_sync_status = 'success'
        item.last_sync_error = None
        item.last_sync_attempt_at = now
        db.commit()
    finally:
        db.close()

    watchlist_response = client.get('/api/stocks/watchlist', headers=auth_headers(token))
    assert watchlist_response.status_code == 200
    item_payload = watchlist_response.json()[0]

    assert item_payload['price_sync_status'] == 'success'
    assert item_payload['last_sync_error'] is None
    assert item_payload['last_sync_attempt_at'] is not None


def test_stocks_watchlist_user_isolation(monkeypatch: pytest.MonkeyPatch):
    token_a = register_and_login('stocks-a@example.com')
    token_b = register_and_login('stocks-b@example.com')

    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_stock_info', classmethod(lambda cls, code: {'shortName': 'NVIDIA'}))
    monkeypatch.setattr(stocks_router.StockDataService, 'fetch_real_price', classmethod(lambda cls, code: None))

    add_response = client.post('/api/stocks/watchlist', headers=auth_headers(token_a), json={'stock_code': 'NVDA'})
    assert add_response.status_code == 201
    assert add_response.json()['price_sync_status'] == 'failed'
    assert add_response.json()['last_sync_error']
    assert add_response.json()['last_sync_attempt_at'] is not None

    watchlist_a = client.get('/api/stocks/watchlist', headers=auth_headers(token_a))
    watchlist_b = client.get('/api/stocks/watchlist', headers=auth_headers(token_b))
    assert watchlist_a.status_code == 200
    assert watchlist_b.status_code == 200
    assert len(watchlist_a.json()) == 1
    assert watchlist_a.json()[0]['price_sync_status'] == 'failed'
    assert watchlist_b.json() == []
