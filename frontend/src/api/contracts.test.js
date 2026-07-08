import { describe, expect, it } from 'vitest'

import {
  normalizeBudgetSummary,
  normalizeDashboardCharts,
  normalizeDashboardSummary,
  normalizeFundamentalsSnapshot,
  normalizeStockAlert,
  normalizeStockIndicators,
  normalizeWatchlistItem
} from '@/api/contracts'

describe('API contract normalizers', () => {
  it('normalizes mixed snake_case and camelCase budget summary payloads', () => {
    const result = normalizeBudgetSummary({
      month: '2026-05',
      total_budget: 5000,
      total_used: 1800,
      total_remaining: 3200,
      items: [{
        id: 1,
        category: 'Food',
        budget: 2000,
        current_spent: 800,
        usagePercent: 40,
        remaining: 1200,
        overBudget: false,
        warning: false,
        status: 'safe'
      }]
    })

    expect(result).toMatchObject({
      totalBudget: 5000,
      totalUsed: 1800,
      totalRemaining: 3200
    })
    expect(result.items[0]).toMatchObject({
      used: 800,
      usageRate: 40,
      over_budget: false
    })
  })

  it('normalizes dashboard summary payloads across API naming styles', () => {
    const result = normalizeDashboardSummary({
      monthly_income: 10000,
      monthlyExpense: 3500,
      monthly_balance: 6500,
      top_expense_category: 'Housing',
      expense_by_category: [{ category: 'Housing', amount: 3500 }],
      recent_transactions: [{ date: '2026-05-01', category: 'Housing', type: 'expense', amount: 3500 }],
      total_budget: 5000,
      totalUsed: 3500,
      total_remaining: 1500,
      budget_items: [{
        category: 'Housing',
        budget: 5000,
        current_spent: 3500,
        remaining: 1500,
        percent_used: 70,
        over_budget: false,
        warning: true,
        status: 'warning'
      }]
    })

    expect(result).toMatchObject({
      monthlyIncome: 10000,
      monthlyExpense: 3500,
      monthlyBalance: 6500,
      topExpenseCategory: 'Housing',
      totalBudget: 5000,
      totalUsed: 3500,
      totalRemaining: 1500
    })
    expect(result.budgetItems[0]).toMatchObject({
      amount: 5000,
      used: 3500,
      usagePercent: 70,
      overBudget: false,
      warning: true
    })
  })

  it('normalizes dashboard chart payloads from snake_case or camelCase responses', () => {
    const result = normalizeDashboardCharts({
      monthlyExpenseTrend: [{ month: '2026-05', amount: 2000 }],
      category_distribution: [{ category: 'Food', amount: 1200 }],
      netIncomeTrend: [{ month: '2026-05', amount: 4000 }],
      budgetUsage: [{
        category: 'Food',
        amount: 2000,
        current_spent: 800,
        percent_used: 40,
        over_budget: false,
        warning: false,
        status: 'safe'
      }]
    })

    expect(result.monthly_expense_trend).toEqual([{ month: '2026-05', amount: 2000 }])
    expect(result.category_distribution).toEqual([{ category: 'Food', amount: 1200 }])
    expect(result.net_income_trend).toEqual([{ month: '2026-05', amount: 4000 }])
    expect(result.budget_usage[0]).toMatchObject({
      currentSpent: 800,
      usagePercent: 40,
      overBudget: false
    })
  })

  it('normalizes watchlist currency and fundamentals source metadata', () => {
    const watchItem = normalizeWatchlistItem({
      id: 7,
      stock_code: 'aapl',
      name: 'Apple',
      currency: 'usd',
      price: '123.45'
    })
    const fundamentals = normalizeFundamentalsSnapshot({
      stock_code: 'aapl',
      source: 'yfinance',
      status: 'success'
    })

    expect(watchItem).toMatchObject({
      stock_code: 'AAPL',
      currency: 'USD',
      price: 123.45
    })
    expect(fundamentals).toMatchObject({
      stock_code: 'AAPL',
      source: 'yfinance',
      provider: 'yfinance'
    })
  })

  it('normalizes stock indicators and alerts', () => {
    const indicators = normalizeStockIndicators({
      watchlist_item_id: '1',
      symbol: '2330.tw',
      latest_close: '1000',
      ma5: '980',
      ma20: '950',
      rsi14: '66.5',
      status: 'ready',
      disclaimer: 'This is informational only and not financial advice.'
    })
    const alert = normalizeStockAlert({
      id: '7',
      user_id: '1',
      watchlist_item_id: '1',
      symbol: '2330.tw',
      condition_type: 'below',
      target_price: '900',
      is_active: 0,
      triggered_at: '2026-07-06T02:00:00Z',
      last_price_at_trigger: '899.5'
    })

    expect(indicators).toMatchObject({
      watchlist_item_id: 1,
      symbol: '2330.TW',
      latest_close: 1000,
      ma20: 950,
      rsi14: 66.5,
      status: 'ready'
    })
    expect(alert).toMatchObject({
      id: 7,
      symbol: '2330.TW',
      condition_type: 'below',
      target_price: 900,
      is_active: false,
      last_price_at_trigger: 899.5
    })
  })
})
