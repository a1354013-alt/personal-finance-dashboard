import { beforeEach, describe, expect, it, vi } from 'vitest'
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
    setActivePinia(createPinia())
  })

  it('loads budgets and renders status', async () => {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    const wrapper = mount(Budgets, { global: { plugins: [pinia, i18n] } })

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('食物')
      expect(wrapper.text()).toContain('20')
    })
  })

  it('submits a budget', async () => {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    const wrapper = mount(Budgets, { global: { plugins: [pinia, i18n] } })

    await wrapper.find('#budget-category').setValue('Food')
    await wrapper.find('#budget-limit').setValue('1500')
    await wrapper.find('form').trigger('submit')

    await vi.waitFor(() => {
      expect(budgetsApi.upsertBudget).toHaveBeenCalledWith({
        category: 'Food',
        amount: 1500,
        month: '2026-05'
      })
      expect(wrapper.text()).toContain('預算已儲存')
      expect(wrapper.text()).toContain('食物')
    })
  })
})
