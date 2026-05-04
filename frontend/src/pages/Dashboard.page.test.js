import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18nInstance } from '@/i18n'
import Dashboard from '@/pages/Dashboard.vue'

// Mock ChartPanel to avoid canvas issues
vi.mock('@/components/ChartPanel.vue', () => ({
  default: {
    name: 'ChartPanel',
    template: '<div class="chart-panel-mock"><slot /></div>',
    props: ['title', 'subtitle', 'loading', 'error', 'labels', 'datasets', 'type']
  }
}))

vi.mock('@/api/dashboard', () => ({
  getDashboardSummary: vi.fn(async () => ({
    monthlyIncome: 10000,
    monthlyExpense: 5000,
    monthlyBalance: 5000,
    topExpenseCategory: 'Housing',
    monthlyTrend: [
      { month: '2026-05', income: 10000, expense: 5000 }
    ],
    expenseByCategory: [
      { category: 'Housing', amount: 3000 },
      { category: 'Food', amount: 2000 }
    ],
    recentTransactions: [
      { date: '2026-05-01', category: 'Housing', type: 'expense', amount: 3000 }
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

describe('Dashboard page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders summary cards correctly', async () => {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    setActivePinia(pinia)
    const wrapper = mount(Dashboard, { 
      global: { 
        plugins: [pinia, i18n],
        stubs: {
          RouterLink: true
        }
      } 
    })
    
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('本月收入')
      expect(wrapper.text()).toContain('NT$ 10,000')
      expect(wrapper.text()).toContain('本月支出')
      expect(wrapper.text()).toContain('NT$ 5,000')
      expect(wrapper.text()).toContain('最大支出分類')
      expect(wrapper.text()).toContain('住房')
    })
  })

  it('renders recent transactions', async () => {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    setActivePinia(pinia)
    const wrapper = mount(Dashboard, { 
      global: { 
        plugins: [pinia, i18n],
        stubs: {
          RouterLink: true
        }
      } 
    })
    
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('最近交易')
      expect(wrapper.text()).toContain('住房')
      expect(wrapper.text()).toContain('- NT$ 3,000')
    })
  })
})
