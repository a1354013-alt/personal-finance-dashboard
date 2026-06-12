import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import { createI18nInstance } from '@/i18n'
import Budgets from '@/pages/Budgets.vue'
import * as budgetsApi from '@/api/budgets'

vi.mock('@/api/budgets', () => ({
  getBudgets: vi.fn(async () => [
    {
      id: 1,
      month: '2026-05',
      category: 'Food',
      amount: 1000,
      current_spent: 200,
      percent_used: 20
    }
  ]),
  getBudgetSummary: vi.fn(async () => ({
    month: '2026-05',
    totalBudget: 1000,
    totalUsed: 200,
    totalRemaining: 800,
    items: [
      {
        id: 1,
        category: 'Food',
        budget: 1000,
        used: 200,
        remaining: 800,
        usageRate: 20,
        status: 'safe'
      }
    ]
  })),
  upsertBudget: vi.fn(async (payload) => ({
    id: 1,
    month: payload.month,
    category: payload.category,
    amount: payload.amount,
    current_spent: 200,
    percent_used: 20
  })),
  deleteBudget: vi.fn(async () => ({}))
}))

describe('Budgets page', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 4, 15, 12, 0, 0))
    localStorage.setItem('locale', 'en')
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('loads budgets with the correct total budget and edit copy', async () => {
    const wrapper = mount(Budgets, {
      global: {
        plugins: [createPinia(), createI18nInstance()]
      }
    })

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Total Budget (All)')
      expect(wrapper.text()).toContain('Food')
      expect(wrapper.text()).toContain('Edit')
    })
  })

  it('submits a budget and keeps the English success copy intact', async () => {
    const wrapper = mount(Budgets, {
      global: {
        plugins: [createPinia(), createI18nInstance()]
      }
    })

    await wrapper.find('#budget-category').setValue('Food')
    await wrapper.find('#budget-limit').setValue('1500')
    await wrapper.find('form').trigger('submit')

    await vi.waitFor(() => {
      expect(budgetsApi.upsertBudget).toHaveBeenCalledWith({
        category: 'Food',
        amount: 1500,
        month: '2026-05'
      })
      expect(wrapper.text()).toContain('Budget saved.')
      expect(wrapper.text()).toContain('Total Budget (All)')
    })
  })
})
