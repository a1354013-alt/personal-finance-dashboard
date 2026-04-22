import { describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/stocks', () => ({
  getWatchlist: vi.fn(async () => []),
  getFilterResults: vi.fn(async () => [{ stock_code: 'AAPL', passed: false, fail_reasons: [], meta: { provider: 'x', ttl_hours: 24, is_stale: true } }]),
  getFilterMetadata: vi.fn(async () => ({ fundamentals_provider: 'yfinance', ttl_hours: 24, timeout_seconds: 8, message: 'ok' })),
  syncWatchlistFundamentals: vi.fn(async () => ([]))
}))

import { useStockStore } from '@/stores/stockStore'
import { getFilterResults, syncWatchlistFundamentals } from '@/api/stocks'

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
})

