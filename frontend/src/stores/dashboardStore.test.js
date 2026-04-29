import { describe, expect, it } from 'vitest'
import { normalizeAiSummary, normalizeBudgetAdvice, normalizeDashboardCharts, normalizeDashboardSummary } from '@/api/contracts'

describe('dashboardStore', () => {
  it('normalizeDashboardSummary coerces numbers and arrays', () => {
    const normalized = normalizeDashboardSummary({
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

  it('normalizeAiSummary returns a stable string', () => {
    expect(normalizeAiSummary(null)).toBe('')
    expect(normalizeAiSummary({ summary: '  hello \n' })).toBe('hello')
    expect(normalizeAiSummary({})).toBe('')
  })

  it('normalizeBudgetAdvice returns a stable string', () => {
    expect(normalizeBudgetAdvice(undefined)).toBe('')
    expect(normalizeBudgetAdvice({ advice: '  do X  ' })).toBe('do X')
    expect(normalizeBudgetAdvice({})).toBe('')
  })

  it('normalizeDashboardCharts returns stable arrays', () => {
    const normalized = normalizeDashboardCharts({
      monthly_expense_trend: null,
      category_distribution: [{ category: 'Food', amount: 50 }],
      net_income_trend: undefined,
      budget_usage: [{ category: 'Food', percent_used: 20 }]
    })

    expect(normalized.monthly_expense_trend).toEqual([])
    expect(normalized.category_distribution).toHaveLength(1)
    expect(normalized.net_income_trend).toEqual([])
    expect(normalized.budget_usage).toHaveLength(1)
  })
})

