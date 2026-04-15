import { describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/stocks', () => ({
  getWatchlist: vi.fn(async () => []),
  getFilterResults: vi.fn(async () => [{ stock_code: 'AAPL', passed: false, fail_reasons: [], meta: { provider: 'x', ttl_hours: 24, is_stale: true } }]),
  getFilterMetadata: vi.fn(async () => ({ fundamentals_provider: 'yfinance', ttl_hours: 24, timeout_seconds: 8, message: 'ok' })),
  syncWatchlistFundamentals: vi.fn(async () => ([]))
}))

import { useStockStore } from '@/stores/stockStore'
import { syncWatchlistFundamentals } from '@/api/stocks'

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
})

