import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import Stocks from '@/pages/Stocks.vue'

const getWatchlistMock = vi.fn(async () => [
  {
    id: 1,
    user_id: 1,
    stock_code: 'NVDA',
    name: 'NVIDIA',
    price: 100,
    date: '2026-04-10',
    volume: 123,
    price_sync_status: 'failed',
    last_sync_error: 'Upstream failed',
    last_sync_attempt_at: '2026-04-10T00:00:00Z'
  }
])

const getFilterResultsMock = vi.fn(async () => [
  { stock_code: 'NVDA', passed: false, fail_reasons: ['No fundamentals cached yet. Sync required.'], fundamentals: null, meta: { provider: 'x', status: null, as_of_date: null, is_stale: true } }
])

const getFilterMetadataMock = vi.fn(async () => ({
  fundamentals_provider: 'test',
  ttl_hours: 24,
  timeout_seconds: 8,
  message: 'metadata'
}))

const addToWatchlistMock = vi.fn(async () => ({
  id: 2,
  user_id: 1,
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
  getWatchlist: (...args) => getWatchlistMock(...args),
  getFilterResults: (...args) => getFilterResultsMock(...args),
  getFilterMetadata: (...args) => getFilterMetadataMock(...args),
  addToWatchlist: (...args) => addToWatchlistMock(...args),
  deleteFromWatchlist: vi.fn(async () => ({})),
  syncAllPrices: vi.fn(async () => ({ message: 'ok', failed_codes: [] })),
  syncSinglePrice: vi.fn(async () => ({ message: 'ok', price_sync_status: 'success' })),
  filterSingleStock: vi.fn(async () => ({ stock_code: 'AAPL', passed: true, fail_reasons: [] })),
  getAiStockExplain: vi.fn(async () => ({ text: 'ok' })),
  syncWatchlistFundamentals: vi.fn(async () => ([]))
}))

describe('Stocks page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getWatchlistMock.mockClear()
    addToWatchlistMock.mockClear()
  })

  it('renders watchlist status and screening sections', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(Stocks, { global: { plugins: [pinia] } })
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('NVDA')
      expect(wrapper.text()).toContain('Upstream failed')
      expect(wrapper.text()).toContain('Failed')
      expect(wrapper.text()).toContain('metadata')
    })
  })

  it('shows queued message on add when sync is pending', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(Stocks, { global: { plugins: [pinia] } })

    await wrapper.find('#stock-code').setValue('AAPL')
    await wrapper.find('form.form-row').trigger('submit')

    await vi.waitFor(() => {
      expect(addToWatchlistMock).toHaveBeenCalled()
      expect(wrapper.text()).toContain('sync is queued')
    })
  })
})
