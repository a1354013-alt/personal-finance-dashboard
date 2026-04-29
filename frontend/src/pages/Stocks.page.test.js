import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import Stocks from '@/pages/Stocks.vue'

const getFilterResultsMock = vi.fn(async () => [
  { stock_code: 'NVDA', passed: false, fail_reasons: ['No fundamentals cached yet. Sync required.'], fundamentals: null, meta: { provider: 'x', status: null, as_of_date: null, ttl_hours: 24, is_stale: true } }
])

const getFilterMetadataMock = vi.fn(async () => ({
  fundamentals_provider: 'test',
  ttl_hours: 24,
  timeout_seconds: 8,
  message: 'metadata'
}))

const getStockDashboardMock = vi.fn(async () => ({
  selected_stock_code: 'NVDA',
  watchlist: [
    {
      id: 1,
      stock_code: 'NVDA',
      name: 'NVIDIA',
      price: 100,
      date: '2026-04-10',
      volume: 123,
      price_sync_status: 'pending',
      last_sync_error: 'Market data sync queued.',
      last_sync_attempt_at: '2026-04-10T00:00:00Z'
    }
  ],
  price_history: [{ trade_date: '2026-04-10', close: 100 }],
  fundamentals: null,
  ai_explanation: ''
}))

const addToWatchlistMock = vi.fn(async () => ({
  id: 2,
  stock_code: 'AAPL',
  name: 'AAPL',
  price: null,
  date: null,
  volume: null,
  price_sync_status: 'pending',
  last_sync_error: null,
  last_sync_attempt_at: null
}))

vi.mock('@/api/stocks', () => ({
  getWatchlist: vi.fn(async () => []),
  getFilterResults: (...args) => getFilterResultsMock(...args),
  getFilterMetadata: (...args) => getFilterMetadataMock(...args),
  getStockDashboard: (...args) => getStockDashboardMock(...args),
  addToWatchlist: (...args) => addToWatchlistMock(...args),
  deleteFromWatchlist: vi.fn(async () => ({})),
  syncAllPrices: vi.fn(async () => ({ message: 'Queued market data sync for 1 watchlist items.' })),
  syncSinglePrice: vi.fn(async () => ({ message: 'Queued market data sync for NVDA.', price_sync_status: 'pending' })),
  filterSingleStock: vi.fn(async () => ({ stock_code: 'AAPL', passed: true, fail_reasons: [] })),
  getAiStockExplain: vi.fn(async () => ({ text: 'ok' })),
  syncWatchlistFundamentals: vi.fn(async () => ([]))
}))

describe('Stocks page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getStockDashboardMock.mockClear()
    addToWatchlistMock.mockClear()
  })

  it('renders watchlist status and price trend sections', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(Stocks, { global: { plugins: [pinia], stubs: { ChartPanel: true } } })
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('NVDA')
      expect(wrapper.text()).toContain('Market data sync queued.')
      expect(wrapper.text()).toContain('Watchlist Grid')
    })
  })

  it('shows queued message on add when background sync is pending', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(Stocks, { global: { plugins: [pinia], stubs: { ChartPanel: true } } })

    await wrapper.find('#stock-code').setValue('AAPL')
    await wrapper.find('form.form-row').trigger('submit')

    await vi.waitFor(() => {
      expect(addToWatchlistMock).toHaveBeenCalled()
      expect(wrapper.text()).toContain('added. Market data sync has been queued')
    })
  })
})
