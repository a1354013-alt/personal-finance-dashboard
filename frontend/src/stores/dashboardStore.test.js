import { describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useDashboardStore } from '@/stores/dashboardStore'

describe('dashboardStore', () => {
  it('normalizeDashboardSummary coerces numbers and arrays', () => {
    setActivePinia(createPinia())
    const store = useDashboardStore()

    const normalized = store.normalizeDashboardSummary({
      total_income: '1234',
      total_expense: 200,
      net_balance: null,
      expense_by_category: null,
      monthly_trend: [{ month: '2026-04', income: 1, expense: 2 }],
      over_budget: undefined
    })

    expect(normalized.total_income).toBe(1234)
    expect(normalized.total_expense).toBe(200)
    expect(normalized.net_balance).toBe(0)
    expect(normalized.expense_by_category).toEqual([])
    expect(normalized.monthly_trend).toHaveLength(1)
    expect(normalized.over_budget).toEqual([])
    expect(normalized.summary_scope.totals).toBe('all_time')
  })
})

