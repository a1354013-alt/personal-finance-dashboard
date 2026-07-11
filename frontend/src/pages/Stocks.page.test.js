import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import { createI18nInstance } from '@/i18n'
import Stocks from '@/pages/Stocks.vue'

const getFilterResultsMock = vi.fn()
const getFilterMetadataMock = vi.fn()
const getStockDashboardMock = vi.fn()
const getStockHoldingsMock = vi.fn()
const getStockPortfolioMock = vi.fn()
const createStockHoldingMock = vi.fn()
const updateStockHoldingMock = vi.fn()
const deleteStockHoldingMock = vi.fn()
const addToWatchlistMock = vi.fn()
const syncWatchlistItemMock = vi.fn()
const analyzeWatchlistItemMock = vi.fn()
const syncSingleFundamentalsMock = vi.fn()
const fetchStockIndicatorsMock = vi.fn()
const listStockAlertsMock = vi.fn()
const createStockAlertMock = vi.fn()
const updateStockAlertMock = vi.fn()
const deleteStockAlertMock = vi.fn()
const checkStockAlertsMock = vi.fn()

vi.mock('@/api/stocks', () => ({
  getWatchlist: vi.fn(async () => []),
  getStockHoldings: (...args) => getStockHoldingsMock(...args),
  getStockPortfolio: (...args) => getStockPortfolioMock(...args),
  createStockHolding: (...args) => createStockHoldingMock(...args),
  updateStockHolding: (...args) => updateStockHoldingMock(...args),
  deleteStockHolding: (...args) => deleteStockHoldingMock(...args),
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
  syncSingleFundamentals: (...args) => syncSingleFundamentalsMock(...args),
  fetchStockIndicators: (...args) => fetchStockIndicatorsMock(...args),
  listStockAlerts: (...args) => listStockAlertsMock(...args),
  createStockAlert: (...args) => createStockAlertMock(...args),
  updateStockAlert: (...args) => updateStockAlertMock(...args),
  deleteStockAlert: (...args) => deleteStockAlertMock(...args),
  checkStockAlerts: (...args) => checkStockAlertsMock(...args)
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

function usItem(overrides = {}) {
  return {
    id: 2,
    stock_code: 'AAPL',
    symbol: 'AAPL',
    name: 'Apple',
    market: 'US',
    exchange: null,
    currency: 'USD',
    price: 150,
    last_price: 150,
    previous_close: 148,
    price_change: 2,
    change_percent: 1.3513,
    date: '2026-07-06',
    volume: 55000000,
    provider: 'fake-us',
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

function holding(overrides = {}) {
  return {
    id: 11,
    stock_code: '2330.TW',
    shares: 10,
    average_cost: 900,
    currency: 'TWD',
    note: 'Core',
    created_at: '2026-07-06T01:00:00Z',
    updated_at: '2026-07-06T01:00:00Z',
    ...overrides
  }
}

function portfolioPayload(overrides = {}) {
  return {
    total_cost: 9000,
    total_market_value: 10000,
    total_unrealized_pnl: 1000,
    total_unrealized_pnl_percent: 11.11,
    holdings_count: 1,
    currency: 'TWD',
    warnings: [],
    positions: [
      {
        holding_id: 11,
        stock_code: '2330.TW',
        stock_name: 'TSMC',
        shares: 10,
        average_cost: 900,
        latest_price: 1000,
        cost_basis: 9000,
        market_value: 10000,
        unrealized_pnl: 1000,
        unrealized_pnl_percent: 11.11,
        allocation_percent: 100,
        currency: 'TWD',
        warning: null,
        updated_at: '2026-07-06T01:00:00Z'
      }
    ],
    ...overrides
  }
}

describe('Stocks page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getFilterResultsMock.mockReset()
    getFilterMetadataMock.mockReset()
    getStockDashboardMock.mockReset()
    getStockHoldingsMock.mockReset()
    getStockPortfolioMock.mockReset()
    createStockHoldingMock.mockReset()
    updateStockHoldingMock.mockReset()
    deleteStockHoldingMock.mockReset()
    addToWatchlistMock.mockReset()
    syncWatchlistItemMock.mockReset()
    analyzeWatchlistItemMock.mockReset()
    syncSingleFundamentalsMock.mockReset()
    fetchStockIndicatorsMock.mockReset()
    listStockAlertsMock.mockReset()
    createStockAlertMock.mockReset()
    updateStockAlertMock.mockReset()
    deleteStockAlertMock.mockReset()
    checkStockAlertsMock.mockReset()
    localStorage.clear()

    getFilterResultsMock.mockResolvedValue([])
    getFilterMetadataMock.mockResolvedValue({
      fundamentals_provider: 'test',
      ttl_hours: 24,
      timeout_seconds: 8,
      message: 'metadata'
    })
    getStockHoldingsMock.mockResolvedValue([])
    getStockPortfolioMock.mockResolvedValue({
      total_cost: 0,
      total_market_value: null,
      total_unrealized_pnl: null,
      total_unrealized_pnl_percent: null,
      holdings_count: 0,
      currency: null,
      warnings: [],
      positions: []
    })
    createStockHoldingMock.mockResolvedValue(holding())
    updateStockHoldingMock.mockResolvedValue(holding({ shares: 12 }))
    deleteStockHoldingMock.mockResolvedValue({})
    getStockDashboardMock.mockResolvedValue(buildDashboard())
    addToWatchlistMock.mockResolvedValue(taiwanItem({ id: 2, stock_code: '0050.TW', symbol: '0050.TW' }))
    syncWatchlistItemMock.mockResolvedValue(taiwanItem())
    fetchStockIndicatorsMock.mockResolvedValue({
      watchlist_item_id: 1,
      symbol: '2330.TW',
      as_of_date: '2026-07-06',
      latest_close: 1000,
      ma5: 980,
      ma20: 950,
      rsi14: 66.5,
      status: 'ready',
      disclaimer: 'This is informational only and not financial advice.'
    })
    listStockAlertsMock.mockResolvedValue([])
    createStockAlertMock.mockResolvedValue({
      id: 10,
      user_id: 1,
      watchlist_item_id: 1,
      symbol: '2330.TW',
      condition_type: 'above',
      target_price: 1050,
      is_active: true,
      triggered_at: null,
      last_checked_at: null,
      last_price_at_trigger: null,
      created_at: '2026-07-06T01:00:00Z',
      updated_at: '2026-07-06T01:00:00Z'
    })
    updateStockAlertMock.mockResolvedValue({
      id: 10,
      user_id: 1,
      watchlist_item_id: 1,
      symbol: '2330.TW',
      condition_type: 'above',
      target_price: 1050,
      is_active: false,
      triggered_at: null,
      last_checked_at: null,
      last_price_at_trigger: null,
      created_at: '2026-07-06T01:00:00Z',
      updated_at: '2026-07-06T01:05:00Z'
    })
    deleteStockAlertMock.mockResolvedValue({})
    checkStockAlertsMock.mockResolvedValue({ checked_count: 1, triggered_count: 1, alerts: [] })
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
      expect(wrapper.text()).toContain('No holdings yet')
    })
  })

  it('renders portfolio summary', async () => {
    getStockHoldingsMock.mockResolvedValue([holding()])
    getStockPortfolioMock.mockResolvedValue(portfolioPayload())

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Portfolio Holdings')
      expect(wrapper.text()).toContain('NT$ 10,000')
      expect(wrapper.text()).toContain('+NT$ 1,000')
      expect(wrapper.text()).toContain('TSMC')
    })
  })

  it('creates a holding', async () => {
    const wrapper = mountStocksPage()

    await wrapper.find('#holding-stock-code').setValue('2330')
    await wrapper.find('#holding-shares').setValue('5')
    await wrapper.find('#holding-average-cost').setValue('880')
    await wrapper.find('form.holding-form').trigger('submit')

    await vi.waitFor(() => {
      expect(createStockHoldingMock).toHaveBeenCalledWith({
        stock_code: '2330',
        shares: 5,
        average_cost: 880,
        note: ''
      })
      expect(wrapper.text()).toContain('Holding saved.')
    })
  })

  it('edits and deletes a holding', async () => {
    getStockHoldingsMock.mockResolvedValue([holding()])
    getStockPortfolioMock.mockResolvedValue(portfolioPayload())

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('TSMC')
    })

    await wrapper.find('.portfolio-position-card .btn.btn-secondary').trigger('click')
    await wrapper.find('#holding-shares').setValue('12')
    await wrapper.find('form.holding-form').trigger('submit')

    await vi.waitFor(() => {
      expect(updateStockHoldingMock).toHaveBeenCalledWith(11, {
        stock_code: '2330.TW',
        shares: 12,
        average_cost: 900,
        note: 'Core'
      })
    })

    await wrapper.find('.portfolio-position-card .btn.btn-danger').trigger('click')
    await vi.waitFor(() => {
      expect(deleteStockHoldingMock).toHaveBeenCalledWith(11)
    })
  })

  it('renders missing price warnings', async () => {
    getStockHoldingsMock.mockResolvedValue([holding()])
    getStockPortfolioMock.mockResolvedValue(portfolioPayload({
      total_market_value: null,
      total_unrealized_pnl: null,
      total_unrealized_pnl_percent: null,
      warnings: ['Latest price unavailable for: 2330.TW. Price-dependent fields are null.'],
      positions: [
        {
          holding_id: 11,
          stock_code: '2330.TW',
          stock_name: 'TSMC',
          shares: 10,
          average_cost: 900,
          latest_price: null,
          cost_basis: 9000,
          market_value: null,
          unrealized_pnl: null,
          unrealized_pnl_percent: null,
          allocation_percent: null,
          currency: 'TWD',
          warning: 'Latest price unavailable for 2330.TW.',
          updated_at: '2026-07-06T01:00:00Z'
        }
      ]
    }))

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Latest price unavailable for: 2330.TW. Price-dependent fields are null.')
      expect(wrapper.text()).toContain('Latest price unavailable for 2330.TW.')
    })
  })

  it('adds a Taiwan stock symbol', async () => {
    const wrapper = mountStocksPage()

    await wrapper.find('#stock-code').setValue('0050')
    await wrapper.findAll('form.form-row')[1].trigger('submit')

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

  it('renders indicator values', async () => {
    getStockDashboardMock.mockResolvedValue(buildDashboard({ watchlist: [taiwanItem()] }))

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(fetchStockIndicatorsMock).toHaveBeenCalledWith(1)
      expect(wrapper.text()).toContain('Technical Indicators')
      expect(wrapper.text()).toContain('MA5')
      expect(wrapper.text()).toContain('NT$ 980')
      expect(wrapper.text()).toContain('66.50')
      expect(wrapper.text()).toContain('not financial advice')
    })
  })

  it('renders insufficient indicator history state', async () => {
    getStockDashboardMock.mockResolvedValue(buildDashboard({ watchlist: [taiwanItem()] }))
    fetchStockIndicatorsMock.mockResolvedValue({
      watchlist_item_id: 1,
      symbol: '2330.TW',
      as_of_date: '2026-07-06',
      latest_close: 1000,
      ma5: 980,
      ma20: null,
      rsi14: null,
      status: 'insufficient_history',
      disclaimer: 'This is informational only and not financial advice.'
    })

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Insufficient price history')
    })
  })

  it('creates an alert for the selected stock', async () => {
    getStockDashboardMock.mockResolvedValue(buildDashboard({ watchlist: [taiwanItem()] }))
    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.find('#alert-price').exists()).toBe(true)
    })

    await wrapper.find('#alert-price').setValue(1050)
    await wrapper.find('form.alert-form').trigger('submit')

    await vi.waitFor(() => {
      expect(createStockAlertMock).toHaveBeenCalledWith(1, { condition_type: 'above', target_price: 1050 })
      expect(wrapper.text()).toContain('Alert created.')
    })
  })

  it('renders triggered alerts and deletes an alert', async () => {
    getStockDashboardMock.mockResolvedValue(buildDashboard({ watchlist: [taiwanItem()] }))
    listStockAlertsMock.mockResolvedValue([
      {
        id: 10,
        user_id: 1,
        watchlist_item_id: 1,
        symbol: '2330.TW',
        condition_type: 'above',
        target_price: 1000,
        is_active: false,
        triggered_at: '2026-07-06T02:00:00Z',
        last_checked_at: '2026-07-06T02:00:00Z',
        last_price_at_trigger: 1050,
        created_at: '2026-07-06T01:00:00Z',
        updated_at: '2026-07-06T02:00:00Z'
      }
    ])

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Triggered')
      expect(wrapper.text()).toContain('Triggered at NT$ 1,050')
    })

    await wrapper.find('.alert-row .btn-danger').trigger('click')

    await vi.waitFor(() => {
      expect(deleteStockAlertMock).toHaveBeenCalledWith(10)
    })
  })

  it('formats each alert with its own watchlist currency', async () => {
    getStockDashboardMock.mockResolvedValue(buildDashboard({ watchlist: [usItem(), taiwanItem()] }))
    listStockAlertsMock.mockResolvedValue([
      {
        id: 20,
        user_id: 1,
        watchlist_item_id: 2,
        symbol: 'AAPL',
        condition_type: 'above',
        target_price: 155,
        is_active: true,
        triggered_at: null,
        last_checked_at: null,
        last_price_at_trigger: null,
        created_at: '2026-07-06T01:00:00Z',
        updated_at: '2026-07-06T01:00:00Z'
      },
      {
        id: 21,
        user_id: 1,
        watchlist_item_id: 1,
        symbol: '2330.TW',
        condition_type: 'below',
        target_price: 900,
        is_active: false,
        triggered_at: '2026-07-06T02:00:00Z',
        last_checked_at: '2026-07-06T02:00:00Z',
        last_price_at_trigger: 880,
        created_at: '2026-07-06T01:00:00Z',
        updated_at: '2026-07-06T02:00:00Z'
      }
    ])

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('AAPL')
      expect(wrapper.text()).toContain('Above US$ 155')
      expect(wrapper.text()).toContain('Below NT$ 900')
      expect(wrapper.text()).toContain('Triggered at NT$ 880')
    })
  })

  it('renders alert API errors', async () => {
    getStockDashboardMock.mockResolvedValue(buildDashboard({ watchlist: [taiwanItem()] }))
    listStockAlertsMock.mockRejectedValue(new Error('Alert API failed'))

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Alert API failed')
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
