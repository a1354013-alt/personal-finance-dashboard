import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18nInstance } from '@/i18n'
import Dashboard from '@/pages/Dashboard.vue'

vi.mock('@/components/ChartPanel.vue', () => ({
  default: {
    name: 'ChartPanel',
    template: '<div class="chart-panel-mock"></div>',
    props: ['title', 'subtitle', 'loading', 'error', 'labels', 'datasets', 'type']
  }
}))

vi.mock('@/api/dashboard', () => ({
  getDashboardSummary: vi.fn(async () => ({
    monthlyIncome: 10000,
    monthlyExpense: 5000,
    monthlyBalance: 5000,
    topExpenseCategory: 'Housing',
    monthlyTrend: [{ month: '2026-05', income: 10000, expense: 5000 }],
    expenseByCategory: [
      { category: 'Housing', amount: 3000 },
      { category: 'Food', amount: 2000 }
    ],
    recentTransactions: [
      { date: '2026-05-01', category: 'Housing', type: 'expense', amount: 3000 }
    ],
    totalBudget: 6000,
    totalUsed: 3000,
    totalRemaining: 3000,
    budgetOverCount: 0,
    budgetWarningCount: 1,
    budgetItems: [
      { category: 'Housing', amount: 6000, used: 3000, remaining: 3000, usagePercent: 50, status: 'safe' }
    ]
  })),
  getDashboardCharts: vi.fn(async () => ({
    monthly_expense_trend: [],
    category_distribution: [],
    net_income_trend: [],
    budget_usage: []
  })),
  getAiSummary: vi.fn(async () => ({ summary: 'AI Summary' })),
  getBudgetAdvice: vi.fn(async () => ({ advice: 'Budget Advice' }))
}))

vi.mock('@/api/reports', () => ({
  exportMonthlyReport: vi.fn(async () => ({
    data: new Blob(['csv']),
    headers: { 'content-disposition': 'attachment; filename="finance-report-2026-05.csv"' }
  }))
}))

describe('Dashboard page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders summary cards and budget health', async () => {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia, i18n],
        stubs: { RouterLink: true }
      }
    })

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('NT$ 10,000')
      expect(wrapper.text()).toContain('NT$ 5,000')
      expect(wrapper.text()).toContain('住房')
      expect(wrapper.text()).toContain('NT$ 6,000')
    })
  })

  it('renders recent transactions and export controls', async () => {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia, i18n],
        stubs: { RouterLink: true }
      }
    })

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('2026-05-01')
      expect(wrapper.text()).toContain('- NT$ 3,000')
      expect(wrapper.find('input[type="month"]').exists()).toBe(true)
    })
  })
})
