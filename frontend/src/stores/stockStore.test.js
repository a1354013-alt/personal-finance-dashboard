import { describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/stocks', () => ({
  getWatchlist: vi.fn(async () => []),
  getFilterResults: vi.fn(async () => [{ stock_code: 'AAPL', passed: false, fail_reasons: [], meta: { provider: 'x', ttl_hours: 24, is_stale: true } }]),
  getFilterMetadata: vi.fn(async () => ({ fundamentals_provider: 'yfinance', ttl_hours: 24, timeout_seconds: 8, message: 'ok' })),
  syncWatchlistFundamentals: vi.fn(async () => ([])),
  syncSingleFundamentals: vi.fn(async () => ({ stock_code: 'AAPL', status: 'pending' })),
  syncWatchlistItem: vi.fn(async () => ({
    id: 1,
    stock_code: '2330.TW',
    currency: 'TWD',
    last_price: 1000,
    sync_status: 'ready'
  })),
  analyzeWatchlistItem: vi.fn(async () => ({
    status: 'ready',
    stock_code: '2330.TW',
    summary: 'This is informational only and not financial advice.',
    recent_price_movement: 'Higher',
    volume_note: 'Volume available',
    risk_notes: ['Volatility'],
    watch_points: ['Freshness'],
    disclaimer: 'This is informational only and not financial advice.'
  })),
  getStockDashboard: vi.fn(async () => ({
    selected_stock_code: 'AAPL',
    watchlist: [],
    price_history: [],
    fundamentals: null,
    ai_explanation: { status: 'sync_required', stock_code: 'AAPL', message: 'sync', explanation: null, can_sync: true }
  }))
}))

import { useStockStore } from '@/stores/stockStore'
import {
  analyzeWatchlistItem,
  getFilterResults,
  syncSingleFundamentals,
  syncWatchlistItem,
  syncWatchlistFundamentals
} from '@/api/stocks'

describe('stockStore', () => {
  it('fetchFilterResults sets results and metadata', async () => {
    setActivePinia(createPinia())
    const store = useStockStore()
    await store.fetchFilterResults()

    expect(store.filterResults).toHaveLength(1)
    expect(store.filterMetadata.fundamentals_provider).toBe('yfinance')
  })

  it('syncFundamentals triggers API and refreshes filter results', async () => {
    setActivePinia(createPinia())
    const store = useStockStore()

    await store.syncFundamentals()
    expect(syncWatchlistFundamentals).toHaveBeenCalledWith({ force: false })
  })

  it('fetchFilterResults normalizes non-happy-path payloads', async () => {
    setActivePinia(createPinia())
    const store = useStockStore()

    getFilterResults.mockResolvedValueOnce([
      {
        stock_code: 'aapl',
        passed: 1,
        fail_reasons: null,
        fundamentals: { stock_code: 'aapl', pe_ratio: '10', pb_ratio: null },
        meta: { provider: 123, ttl_hours: '24', is_stale: 0 }
      }
    ])

    await store.fetchFilterResults()

    const row = store.filterResults[0]
    expect(row.stock_code).toBe('AAPL')
    expect(row.passed).toBe(true)
    expect(row.fail_reasons).toEqual([])
    expect(row.fundamentals.pe_ratio).toBe(10)
    expect(row.meta.provider).toBe('123')
    expect(row.meta.is_stale).toBe(false)
  })

  it('syncFundamentals surfaces errors and resets syncing flag', async () => {
    setActivePinia(createPinia())
    const store = useStockStore()

    syncWatchlistFundamentals.mockRejectedValueOnce(new Error('boom'))

    await expect(store.syncFundamentals()).rejects.toThrow('boom')
    expect(store.fundamentalsSyncing).toBe(false)
    expect(store.fundamentalsError).toBe('boom')
  })

  it('fetchDashboard normalizes dashboard payloads', async () => {
    setActivePinia(createPinia())
    const store = useStockStore()

    await store.fetchDashboard('AAPL')

    expect(store.dashboard.selected_stock_code).toBe('AAPL')
    expect(store.dashboard.ai_explanation.status).toBe('sync_required')
    expect(store.watchlist).toEqual([])
  })

  it('syncSingleFundamentals refreshes dashboard and filter results', async () => {
    setActivePinia(createPinia())
    const store = useStockStore()

    await store.syncSingleFundamentals('AAPL')

    expect(syncSingleFundamentals).toHaveBeenCalledWith('AAPL', { force: false })
    expect(store.syncingFundamentalsCodes).toEqual([])
  })

  it('syncWatchlistItem normalizes Taiwan stock price data', async () => {
    setActivePinia(createPinia())
    const store = useStockStore()
    store.watchlist = [{ id: 1, stock_code: '2330.TW', price_sync_status: 'pending' }]

    const result = await store.syncWatchlistItem(1)

    expect(syncWatchlistItem).toHaveBeenCalledWith(1)
    expect(result.stock_code).toBe('2330.TW')
    expect(result.last_price).toBe(1000)
    expect(result.currency).toBe('TWD')
    expect(store.syncingItemIds).toEqual([])
  })

  it('analyzeWatchlistItem stores structured AI interpretation', async () => {
    setActivePinia(createPinia())
    const store = useStockStore()

    const result = await store.analyzeWatchlistItem(1)

    expect(analyzeWatchlistItem).toHaveBeenCalledWith(1)
    expect(result.disclaimer).toContain('not financial advice')
    expect(store.aiAnalysisById[1].risk_notes).toEqual(['Volatility'])
    expect(store.analyzingIds).toEqual([])
  })
})
