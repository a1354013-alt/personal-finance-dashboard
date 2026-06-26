import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import { createI18nInstance } from '@/i18n'
import Stocks from '@/pages/Stocks.vue'

const getFilterResultsMock = vi.fn()
const getFilterMetadataMock = vi.fn()
const getStockDashboardMock = vi.fn()
const addToWatchlistMock = vi.fn()
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
  filterSingleStock: vi.fn(async () => ({ stock_code: 'AAPL', passed: true, fail_reasons: [] })),
  getAiStockExplain: vi.fn(async () => ({ text: 'ok' })),
  syncWatchlistFundamentals: vi.fn(async () => ([])),
  syncSingleFundamentals: (...args) => syncSingleFundamentalsMock(...args)
}))

function buildDashboard(aiExplanation) {
  return {
    selected_stock_code: 'NVDA',
    watchlist: [
      {
        id: 1,
        stock_code: 'NVDA',
        name: 'NVIDIA',
        currency: 'USD',
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
    ai_explanation: aiExplanation
  }
}

function mountStocksPage(locale = 'zh-TW') {
  localStorage.setItem('locale', locale)
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
    syncSingleFundamentalsMock.mockReset()

    getFilterResultsMock.mockResolvedValue([
      {
        stock_code: 'NVDA',
        passed: false,
        fail_reasons: ['Fundamentals data is not available yet. Sync required.'],
        fundamentals: null,
        meta: { provider: 'x', status: 'sync_required', as_of_date: null, ttl_hours: 24, is_stale: true }
      }
    ])
    getFilterMetadataMock.mockResolvedValue({
      fundamentals_provider: 'test',
      ttl_hours: 24,
      timeout_seconds: 8,
      message: 'metadata'
    })
    addToWatchlistMock.mockResolvedValue({
      id: 2,
      stock_code: 'AAPL',
      name: 'AAPL',
      currency: 'USD',
      price: null,
      date: null,
      volume: null,
      price_sync_status: 'pending',
      last_sync_error: null,
      last_sync_attempt_at: null
    })
    syncSingleFundamentalsMock.mockResolvedValue({ stock_code: 'NVDA', status: 'pending' })
  })

  it('renders friendly sync-required AI state without fallback debug text', async () => {
    getStockDashboardMock.mockResolvedValue(
      buildDashboard({
        status: 'sync_required',
        stock_code: 'NVDA',
        message: 'Fundamentals data is not available yet. Please sync first.',
        explanation: null,
        can_sync: true,
        request_id: 'abc123'
      })
    )

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('目前尚未取得 NVDA 的基本面資料')
    })

    expect(wrapper.text()).toContain('同步基本面資料')
    expect(wrapper.text()).not.toContain('[Fallback AI]')
    expect(wrapper.text()).not.toContain('request_id')
  })

  it('sync button triggers single-stock fundamentals sync and shows queued message', async () => {
    getStockDashboardMock
      .mockResolvedValueOnce(
        buildDashboard({
          status: 'sync_required',
          stock_code: 'NVDA',
          message: 'Fundamentals data is not available yet. Please sync first.',
          explanation: null,
          can_sync: true
        })
      )
      .mockResolvedValue(
        buildDashboard({
          status: 'sync_queued',
          stock_code: 'NVDA',
          message: 'Fundamentals sync has been queued. Please retry later.',
          explanation: null,
          can_sync: true
        })
      )

    const wrapper = mountStocksPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('同步基本面資料')
    })

    await vi.waitFor(() => {
      expect(wrapper.find('.ai-card .btn.btn-primary').exists()).toBe(true)
    })

    const syncButton = wrapper.find('.ai-card .btn.btn-primary')
    await syncButton.trigger('click')

    await vi.waitFor(() => {
      expect(syncSingleFundamentalsMock).toHaveBeenCalledWith('NVDA', { force: false })
      expect(wrapper.text()).toContain('已開始同步基本面資料')
    })
  })

  it('renders successful AI explanation content', async () => {
    getStockDashboardMock.mockResolvedValue(
      buildDashboard({
        status: 'ready',
        stock_code: 'NVDA',
        message: null,
        explanation: 'NVDA currently does not pass the baseline screen.',
        can_sync: true,
        meta: { provider: 'fallback', is_fallback: true, error: null }
      })
    )

    const wrapper = mountStocksPage('en')

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('NVDA currently does not pass the baseline screen.')
    })

    expect(wrapper.text()).not.toContain('[Fallback AI]')
    expect(wrapper.text()).not.toContain('request_id')
  })

  it('shows the stock currency and fundamentals source from the current contracts', async () => {
    getStockDashboardMock.mockResolvedValue(
      {
        ...buildDashboard({
          status: 'ready',
          stock_code: 'NVDA',
          message: null,
          explanation: 'ok',
          can_sync: true
        }),
        fundamentals: {
          stock_code: 'NVDA',
          source: 'yfinance',
          status: 'success',
          pe_ratio: 20.1,
          pb_ratio: 5.2,
          dividend_yield: 1.1,
          revenue_growth: 12.3,
          eps: 4.5
        }
      }
    )

    const wrapper = mountStocksPage('en')

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('US$ 100')
      expect(wrapper.text()).toContain('yfinance')
    })
  })

  it('renders each watchlist item with its own currency when the watchlist mixes markets', async () => {
    getStockDashboardMock.mockResolvedValue({
      selected_stock_code: 'AAPL',
      watchlist: [
        {
          id: 1,
          stock_code: 'AAPL',
          name: 'Apple',
          currency: 'USD',
          price: 100,
          date: '2026-04-10',
          volume: 123,
          price_sync_status: 'success',
          last_sync_error: null,
          last_sync_attempt_at: '2026-04-10T00:00:00Z'
        },
        {
          id: 2,
          stock_code: '2330.TW',
          name: 'TSMC',
          currency: 'TWD',
          price: 950,
          date: '2026-04-10',
          volume: 456,
          price_sync_status: 'success',
          last_sync_error: null,
          last_sync_attempt_at: '2026-04-10T00:00:00Z'
        }
      ],
      price_history: [{ trade_date: '2026-04-10', close: 100 }],
      fundamentals: null,
      ai_explanation: {
        status: 'ready',
        stock_code: 'AAPL',
        message: null,
        explanation: 'ok',
        can_sync: true
      }
    })

    const wrapper = mountStocksPage('en')

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('US$ 100')
      expect(wrapper.text()).toContain('NT$ 950')
    })

    expect(wrapper.text()).not.toContain('US$ 950')
  })
})
