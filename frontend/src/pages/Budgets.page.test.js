import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import Budgets from '@/pages/Budgets.vue'

vi.mock('@/api/budgets', () => ({
  getBudgets: vi.fn(async () => [
    {
      id: 1,
      user_id: 1,
      category: 'Food',
      monthly_limit: 1000,
      current_spent: 200,
      percent_used: 20,
      over_budget: false,
      created_at: '2026-04-10T00:00:00Z'
    }
  ]),
  createBudget: vi.fn(async (payload) => ({
    id: 1,
    user_id: 1,
    category: payload.category,
    monthly_limit: payload.monthly_limit,
    current_spent: 200,
    percent_used: 20,
    over_budget: false,
    created_at: '2026-04-10T00:00:00Z'
  })),
  deleteBudget: vi.fn(async () => ({}))
}))

describe('Budgets page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('loads budgets and renders status', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(Budgets, { global: { plugins: [pinia] } })
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Food')
      expect(wrapper.text()).toContain('20.0% used')
    })
  })

  it('submits a budget and shows success message', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(Budgets, { global: { plugins: [pinia] } })

    await wrapper.find('#budget-category').setValue('Food')
    await wrapper.find('#budget-limit').setValue('1500')
    await wrapper.find('form').trigger('submit')

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Budget saved successfully.')
    })
  })
})
