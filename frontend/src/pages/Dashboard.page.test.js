import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18nInstance } from '@/i18n'
import { exportMonthlyReport } from '@/api/reports'
import Dashboard from '@/pages/Dashboard.vue'
import { getDashboardCharts } from '@/api/dashboard'

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
    ],
    monthlyForecast: {
      projectedIncome: 12000,
      projectedExpense: 7000,
      projectedBalance: 5000,
      actualIncomeToDate: 10000,
      actualExpenseToDate: 5000,
      recurringIncomePending: 2000,
      recurringExpensePending: 2000,
      overdueRecurringExpensePending: 500,
      forecastWarnings: []
    },
    unbudgetedSpending: [
      { category: 'Travel', amount: 450, transactionCount: 2 }
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
  exportMonthlyReport: vi.fn(async (month, format) => ({
    data: new Blob([format]),
    headers: {
      'content-disposition': `attachment; filename="finance-report-${month}.${format}"`
    }
  }))
}))

describe('Dashboard page', () => {
  let originalCreateElement
  let createObjectURLSpy
  let revokeObjectURLSpy
  let clickSpy

  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 4, 15, 12, 0, 0))
    setActivePinia(createPinia())
    originalCreateElement = document.createElement.bind(document)
    if (!URL.createObjectURL) {
      URL.createObjectURL = () => 'blob:placeholder'
    }
    if (!URL.revokeObjectURL) {
      URL.revokeObjectURL = () => {}
    }
    createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test')
    revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    clickSpy = vi.fn()

    vi.spyOn(document, 'createElement').mockImplementation((tagName) => {
      const element = originalCreateElement(tagName)
      if (tagName === 'a') {
        element.click = clickSpy
      }
      return element
    })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
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

  it('renders forecast and unbudgeted spending sections', async () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [createPinia(), createI18nInstance()],
        stubs: { RouterLink: true }
      }
    })

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('每月預測')
      expect(wrapper.text()).toContain('未編列預算的支出')
      expect(wrapper.text()).toContain('NT$ 12,000')
      expect(wrapper.text()).toContain('NT$ 450')
      expect(wrapper.text()).toContain('包含逾期但仍待處理的定期項目：NT$ 500')
    })
  })

  it('loads charts for dashboard visualizations', async () => {
    mount(Dashboard, {
      global: {
        plugins: [createPinia(), createI18nInstance()],
        stubs: { RouterLink: true }
      }
    })

    await vi.waitFor(() => {
      expect(getDashboardCharts).toHaveBeenCalled()
    })
  })

  it('clicking Export CSV calls exportMonthlyReport(month, "csv")', async () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [createPinia(), createI18nInstance()],
        stubs: { RouterLink: true }
      }
    })

    await wrapper.find('button.btn-secondary').trigger('click')

    expect(exportMonthlyReport).toHaveBeenCalledWith('2026-05', 'csv')
    expect(createObjectURLSpy).toHaveBeenCalled()
    expect(clickSpy).toHaveBeenCalled()
    expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:test')
  })

  it('clicking Export PDF calls exportMonthlyReport(month, "pdf")', async () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [createPinia(), createI18nInstance()],
        stubs: { RouterLink: true }
      }
    })

    await wrapper.find('button.btn-primary').trigger('click')

    expect(exportMonthlyReport).toHaveBeenCalledWith('2026-05', 'pdf')
  })

  it('shows an error message when export fails', async () => {
    exportMonthlyReport.mockRejectedValueOnce(new Error('Export failed'))
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [createPinia(), createI18nInstance()],
        stubs: { RouterLink: true }
      }
    })

    await wrapper.find('button.btn-secondary').trigger('click')

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Export failed')
    })
  })
})
