import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import { createI18nInstance } from '@/i18n'
import RecurringTransactions from '@/pages/RecurringTransactions.vue'

const getRecurringTransactionsMock = vi.fn(async () => [
  {
    id: 1,
    amount: 1200,
    category: 'Housing',
    type: 'expense',
    note: 'Rent',
    frequency: 'monthly',
    start_date: '2026-07-01',
    end_date: null,
    next_run_date: '2026-07-15',
    is_active: true
  }
])
const createRecurringTransactionMock = vi.fn(async () => ({ id: 2 }))
const updateRecurringTransactionMock = vi.fn(async () => ({ id: 1 }))
const deactivateRecurringTransactionMock = vi.fn(async () => ({ id: 1 }))
const deleteRecurringTransactionMock = vi.fn(async () => ({}))

vi.mock('@/api/recurringTransactions', () => ({
  getRecurringTransactions: (...args) => getRecurringTransactionsMock(...args),
  createRecurringTransaction: (...args) => createRecurringTransactionMock(...args),
  updateRecurringTransaction: (...args) => updateRecurringTransactionMock(...args),
  deactivateRecurringTransaction: (...args) => deactivateRecurringTransactionMock(...args),
  deleteRecurringTransaction: (...args) => deleteRecurringTransactionMock(...args)
}))

describe('Recurring transactions page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getRecurringTransactionsMock.mockClear()
    createRecurringTransactionMock.mockClear()
    updateRecurringTransactionMock.mockClear()
    deactivateRecurringTransactionMock.mockClear()
    deleteRecurringTransactionMock.mockClear()
  })

  it('renders existing recurring transactions', async () => {
    const wrapper = mount(RecurringTransactions, {
      global: { plugins: [createPinia(), createI18nInstance()] }
    })

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Recurring Schedule')
      expect(wrapper.text()).toContain('NT$ 1,200')
      expect(wrapper.text()).toContain('2026-07-15')
    })
  })

  it('creates, deactivates, and deletes through the store flow', async () => {
    const wrapper = mount(RecurringTransactions, {
      global: { plugins: [createPinia(), createI18nInstance()] }
    })

    await wrapper.find('#recurring-amount').setValue('99')
    await wrapper.find('#recurring-type').setValue('expense')
    await wrapper.find('#recurring-category').setValue('Food')
    await wrapper.find('#recurring-frequency').setValue('weekly')
    await wrapper.find('#recurring-start').setValue('2026-07-10')
    await wrapper.find('form.form-row').trigger('submit')

    await vi.waitFor(() => {
      expect(createRecurringTransactionMock).toHaveBeenCalled()
    })

    const buttons = wrapper.findAll('tbody button')
    await buttons[1].trigger('click')
    await buttons[2].trigger('click')

    expect(deactivateRecurringTransactionMock).toHaveBeenCalledWith(1)
    expect(deleteRecurringTransactionMock).toHaveBeenCalledWith(1)
  })

  it('edits an existing recurring transaction', async () => {
    const wrapper = mount(RecurringTransactions, {
      global: { plugins: [createPinia(), createI18nInstance()] }
    })

    await vi.waitFor(() => {
      expect(wrapper.findAll('tbody button').length).toBeGreaterThanOrEqual(3)
    })
    await wrapper.findAll('tbody button')[0].trigger('click')
    await vi.waitFor(() => {
      expect(wrapper.find('#recurring-amount').element.value).toBe('1200')
    })
    await wrapper.find('#recurring-amount').setValue('1500')
    await wrapper.find('form.form-row').trigger('submit')

    await vi.waitFor(() => {
      expect(updateRecurringTransactionMock).toHaveBeenCalledWith(1, expect.objectContaining({ amount: 1500 }))
    })
  })
})
