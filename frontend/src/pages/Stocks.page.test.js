import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import { createI18nInstance } from '@/i18n'
import Stocks from '@/pages/Stocks.vue'

const getFilterResultsMock = vi.fn()
const getFilterMetadataMock = vi.fn()
const getStockDashboardMock = vi.fn()
const addToWatchlistMock = vi.fn()
const syncWatchlistItemMock = vi.fn()
const analyzeWatchlistItemMock = vi.fn()
const syncSingleFundamentalsMock = vi.fn()

vi.mock('@/api/stocks', () => ({
  getWatchlist: vi.fn(async () => []),
  getFilterResults: (...args) => getFilterResultsMock(...args),
  getFilterMetadata: (...args) => getFilterMetadataMock(...args),
  getStockDashboard: (...args) => getStockDashboardMock(...args),
  addToWatchlist: (...args) => addToWatchlistMock(...args),
  deleteFromWatchlist: vi.fn(async () => ({})),
  syncAllPrices: vi.fn(async () => ({ message: 'Queued market data sync for 1 watchlist items.' })),
  syncSinglePrice: vi.fn(async () => ({ message: 'Queued market data sync for NVDA.', price_sync_status: 'pending' })),
  syncWatchlistItem: (...args) => syncWatchlistItemMock(...args),
  analyzeWatchlistItem: (...args) => analyzeWatchlistItemMock(...args),
  filterSingleStock: vi.fn(async () => ({ stock_code: 'AAPL', passed: true, fail_reasons: [] })),
  getAiStockExplain: vi.fn(async () => ({ text: 'ok' })),
  syncWatchlistFundamentals: vi.fn(async () => ([])),
  syncSingleFundamentals: (...args) => syncSingleFundamentalsMock(...args)
}))

function buildDashboard({ watchlist = [], aiExplanation = null, fundamentals = null } = {}) {
  return {
    selected_stock_code: watchlist[0]?.stock_code || null,
    watchlist,
    price_history: watchlist[0]?.last_price ? [{ trade_date: '2026-07-06', close: watchlist[0].last_price }] : [],
    fundamentals,
    ai_explanation: aiExplanation
  }
}

function taiwanItem(overrides = {}) {
  return {
    id: 1,
    stock_code: '2330.TW',
    symbol: '2330.TW',
    name: 'TSMC',
    market: 'Taiwan',
    exchange: 'TWSE',
    currency: 'TWD',
    price: 1000,
    last_price: 1000,
    previous_close: 950,
    price_change: 50,
    change_percent: 5.2631,
    date: '2026-07-06',
    volume: 12345678,
    provider: 'fake-taiwan',
    price_updated_at: '2026-07-06T01:00:00Z',
    sync_status: 'ready',
    sync_required: false,
    sync_error: null,
    price_sync_status: 'success',
    last_sync_error: null,
    last_sync_attempt_at: '2026-07-06T01:00:00Z',
    ...overrides
  }
}

function mountStocksPage() {
  localStorage.setItem('locale', 'en')
  return mount(Stocks, {
    global: {
      plugins: [createPinia(), createI18nInstance()],
      stubs: { ChartPanel: true }
    }
  })
}

describe('Stocks page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getFilterResultsMock.mockReset()
    getFilterMetadataMock.mockReset()
    getStockDashboardMock.mockReset()
    addToWatchlistMock.mockReset()
    syncWatchlistItemMock.mockReset()
    analyzeWatchlistItemMock.mockReset()
    syncSingleFundamentalsMock.mockReset()
    localStorage.clear()

    getFilterResultsMock.mockResolvedValue([])
    getFilterMetadataMock.mockResolvedValue({
      fundamentals_provider: 'test',
      ttl_hours: 24,
      timeout_seconds: 8,
      message: 'metadata'
    })
    getStockDashboardMock.mockResolvedValue(buildDashboard())
    addToWatchlistMock.mockResolvedValue(taiwanItem({ id: 2, stock_code: '0050.TW', symbol: '0050.TW' }))
    syncWatchlistItemMock.mockResolvedValue(taiwanItem())
    analyzeWatchlistItemMock.mockResolvedValue({
      status: 'ready',
      stock_code: '2330.TW',
      summary: '2330.TW data interpretation. This is informational only and not financial advice.',
      recent_price_movement: 'The latest cached price is higher by 50.00 TWD (5.26%).',
      volume_note: 'Latest cached volume is 12,345,678 shares.',
      risk_notes: ['Single-symbol concentration can increase volatility.'],
      watch_points: ['Check whether the latest price timestamp is current.'],
      disclaimer: 'This is informational only and not financial advice.'
    })
  })

  it('renders empty state', async () => {
    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Build your market dashboard')
    })
  })

  it('adds a Taiwan stock symbol', async () => {
    const wrapper = mountStocksPage()

    await wrapper.find('#stock-code').setValue('0050')
    await wrapper.find('form.form-row').trigger('submit')

    await vi.waitFor(() => {
      expect(addToWatchlistMock).toHaveBeenCalledWith('0050')
      expect(wrapper.text()).toContain('0050.TW')
    })
  })

  it('displays stock price data', async () => {
    getStockDashboardMock.mockResolvedValue(buildDashboard({ watchlist: [taiwanItem()] }))

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('2330.TW')
      expect(wrapper.text()).toContain('NT$ 1,000')
      expect(wrapper.text()).toContain('+50.00 (+5.26%)')
      expect(wrapper.text()).toContain('Taiwan / TWSE')
    })
  })

  it('displays sync error state', async () => {
    getStockDashboardMock.mockResolvedValue(
      buildDashboard({
        watchlist: [
          taiwanItem({
            price: null,
            last_price: null,
            price_change: null,
            change_percent: null,
            sync_status: 'error',
            sync_required: true,
            sync_error: 'Unable to fetch latest price data from the upstream provider.',
            price_sync_status: 'failed'
          })
        ]
      })
    )

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Unable to fetch latest price data from the upstream provider.')
    })
  })

  it('displays AI interpretation and disclaimer', async () => {
    getStockDashboardMock.mockResolvedValue(buildDashboard({ watchlist: [taiwanItem()] }))
    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.find('.watchlist-tile').exists()).toBe(true)
    })

    await wrapper.findAll('.watchlist-tile .btn.btn-secondary')[0].trigger('click')

    await vi.waitFor(() => {
      expect(analyzeWatchlistItemMock).toHaveBeenCalledWith(1)
      expect(wrapper.text()).toContain('2330.TW data interpretation')
      expect(wrapper.text()).toContain('This is informational only and not financial advice.')
    })
  })

  it('does not crash when API returns unsupported or sync_required', async () => {
    getStockDashboardMock.mockResolvedValue(
      buildDashboard({
        watchlist: [taiwanItem({ sync_status: 'unsupported', sync_required: true })],
        aiExplanation: { status: 'unsupported', stock_code: '2330.TW', can_sync: false }
      })
    )

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('The current data source does not provide fundamentals')
      expect(wrapper.text()).toContain('2330.TW')
    })
  })
})
