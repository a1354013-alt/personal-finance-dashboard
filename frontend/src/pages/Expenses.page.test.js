import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import { createI18nInstance } from '@/i18n'
import Expenses from '@/pages/Expenses.vue'

const getExpensesMock = vi.fn(async () => [
  { id: 1, amount: 120, category: 'Food', type: 'expense', date: '2026-04-10', note: 'Lunch' }
])
const createExpenseMock = vi.fn(async () => ({ id: 2 }))
const deleteExpenseMock = vi.fn(async () => ({}))

vi.mock('@/api/expenses', () => ({
  getExpenses: (...args) => getExpensesMock(...args),
  createExpense: (...args) => createExpenseMock(...args),
  deleteExpense: (...args) => deleteExpenseMock(...args)
}))

describe('Expenses page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getExpensesMock.mockClear()
    createExpenseMock.mockClear()
    deleteExpenseMock.mockClear()
  })

  it('loads expenses and shows the table row', async () => {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    setActivePinia(pinia)
    const wrapper = mount(Expenses, { global: { plugins: [pinia, i18n] } })
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Lunch')
      expect(wrapper.text()).toContain('食物')
    })
  })

  it('creates and deletes an expense via store flow', async () => {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    setActivePinia(pinia)
    const wrapper = mount(Expenses, { global: { plugins: [pinia, i18n] } })

    await wrapper.find('#expense-amount').setValue('99.5')
    await wrapper.find('#expense-type').setValue('expense')
    await wrapper.find('#expense-category').setValue('Food')
    await wrapper.find('#expense-date').setValue('2026-04-10')
    await wrapper.find('#expense-note').setValue('Coffee')
    await wrapper.find('form.form-row').trigger('submit')

    await vi.waitFor(() => {
      expect(createExpenseMock).toHaveBeenCalled()
      expect(getExpensesMock).toHaveBeenCalled()
    })

    await wrapper.find('button.btn.btn-danger').trigger('click')
    await vi.waitFor(() => {
      expect(deleteExpenseMock).toHaveBeenCalled()
    })
  })

  it('resets the filter UI and refetches unfiltered data after adding a record', async () => {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    setActivePinia(pinia)
    const wrapper = mount(Expenses, { global: { plugins: [pinia, i18n] } })

    await vi.waitFor(() => {
      expect(getExpensesMock).toHaveBeenCalledWith({})
    })

    await wrapper.find('#filter-type').setValue('income')
    await vi.waitFor(() => {
      expect(getExpensesMock).toHaveBeenLastCalledWith({ type: 'income' })
    })

    await wrapper.find('#expense-amount').setValue('88')
    await wrapper.find('#expense-type').setValue('expense')
    await wrapper.find('#expense-category').setValue('Food')
    await wrapper.find('#expense-date').setValue('2026-04-10')
    await wrapper.find('form.form-row').trigger('submit')

    await vi.waitFor(() => {
      expect(createExpenseMock).toHaveBeenCalled()
      expect(getExpensesMock).toHaveBeenLastCalledWith({})
      expect(wrapper.find('#filter-type').element.value).toBe('')
    })
  })
})
