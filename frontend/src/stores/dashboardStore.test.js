import { describe, expect, it } from 'vitest'
import { normalizeAiSummary, normalizeBudgetAdvice, normalizeDashboardCharts, normalizeDashboardSummary } from '@/api/contracts'

describe('dashboardStore', () => {
  it('normalizeDashboardSummary coerces numbers and arrays', () => {
    const normalized = normalizeDashboardSummary({
      monthlyIncome: '1234',
      monthlyExpense: 200,
      monthlyBalance: null,
      topExpenseCategory: 'Housing',
      expenseByCategory: null,
      monthlyTrend: [{ month: '2026-04', income: 1, expense: 2 }],
      recentTransactions: undefined
    })

    expect(normalized.monthlyIncome).toBe(1234)
    expect(normalized.monthlyExpense).toBe(200)
    expect(normalized.monthlyBalance).toBe(0)
    expect(normalized.topExpenseCategory).toBe('Housing')
    expect(normalized.expenseByCategory).toEqual([])
    expect(normalized.monthlyTrend).toHaveLength(1)
    expect(normalized.recentTransactions).toEqual([])
    expect(normalized.budgetItems).toEqual([])
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
      budget_usage: [{ category: 'Food', amount: 100, currentSpent: 20, usagePercent: 20, status: 'safe' }]
    })

    expect(normalized.monthly_expense_trend).toEqual([])
    expect(normalized.category_distribution).toHaveLength(1)
    expect(normalized.net_income_trend).toEqual([])
    expect(normalized.budget_usage).toHaveLength(1)
    expect(normalized.budget_usage[0].amount).toBe(100)
  })
})
