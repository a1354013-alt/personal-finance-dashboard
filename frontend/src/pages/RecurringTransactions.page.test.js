import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import { createI18nInstance } from '@/i18n'
import RecurringTransactions from '@/pages/RecurringTransactions.vue'

const recurringItems = [
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
  },
  {
    id: 2,
    amount: 400,
    category: 'Utilities',
    type: 'expense',
    note: 'Paused bill',
    frequency: 'monthly',
    start_date: '2026-07-02',
    end_date: null,
    next_run_date: null,
    is_active: false
  }
]

const recurringOccurrences = [
  {
    id: 11,
    recurring_transaction_id: 1,
    user_id: 1,
    scheduled_date: '2026-07-15',
    status: 'pending',
    generated_expense_id: null,
    recurring_transaction: recurringItems[0]
  },
  {
    id: 12,
    recurring_transaction_id: 2,
    user_id: 1,
    scheduled_date: '2026-07-20',
    status: 'generated',
    generated_expense_id: 77,
    recurring_transaction: {
      ...recurringItems[1],
      is_active: true
    }
  }
]

const getRecurringTransactionsMock = vi.fn(async () => recurringItems)
const getRecurringOccurrencesMock = vi.fn(async () => recurringOccurrences)
const generateCurrentMonthRecurringTransactionsMock = vi.fn(async () => ({
  created_count: 1,
  skipped_count: 0,
  already_existing_count: 1
}))
const generateRecurringOccurrenceMock = vi.fn(async () => ({ summary: { created_count: 1, skipped_count: 0, already_existing_count: 0 } }))
const skipRecurringOccurrenceMock = vi.fn(async () => ({ summary: { created_count: 0, skipped_count: 1, already_existing_count: 0 } }))
const createRecurringTransactionMock = vi.fn(async () => ({ id: 3 }))
const updateRecurringTransactionMock = vi.fn(async () => ({ id: 1 }))
const deactivateRecurringTransactionMock = vi.fn(async () => ({ id: 1 }))
const deleteRecurringTransactionMock = vi.fn(async () => ({}))
const getDashboardSummaryMock = vi.fn(async () => ({ monthlyForecast: {} }))
const getDashboardChartsMock = vi.fn(async () => ({}))
const getAiSummaryMock = vi.fn(async () => ({ summary: '' }))
const getBudgetAdviceMock = vi.fn(async () => ({ advice: '' }))
const getExpensesMock = vi.fn(async () => [])

vi.mock('@/api/recurringTransactions', () => ({
  getRecurringTransactions: (...args) => getRecurringTransactionsMock(...args),
  getRecurringOccurrences: (...args) => getRecurringOccurrencesMock(...args),
  generateCurrentMonthRecurringTransactions: (...args) => generateCurrentMonthRecurringTransactionsMock(...args),
  generateRecurringOccurrence: (...args) => generateRecurringOccurrenceMock(...args),
  skipRecurringOccurrence: (...args) => skipRecurringOccurrenceMock(...args),
  createRecurringTransaction: (...args) => createRecurringTransactionMock(...args),
  updateRecurringTransaction: (...args) => updateRecurringTransactionMock(...args),
  deactivateRecurringTransaction: (...args) => deactivateRecurringTransactionMock(...args),
  deleteRecurringTransaction: (...args) => deleteRecurringTransactionMock(...args)
}))

vi.mock('@/api/dashboard', () => ({
  getDashboardSummary: (...args) => getDashboardSummaryMock(...args),
  getDashboardCharts: (...args) => getDashboardChartsMock(...args),
  getAiSummary: (...args) => getAiSummaryMock(...args),
  getBudgetAdvice: (...args) => getBudgetAdviceMock(...args)
}))

vi.mock('@/api/expenses', () => ({
  getExpenses: (...args) => getExpensesMock(...args),
  createExpense: vi.fn(),
  updateExpense: vi.fn(),
  deleteExpense: vi.fn()
}))

describe('Recurring transactions page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    for (const mockFn of [
      getRecurringTransactionsMock,
      getRecurringOccurrencesMock,
      generateCurrentMonthRecurringTransactionsMock,
      generateRecurringOccurrenceMock,
      skipRecurringOccurrenceMock,
      createRecurringTransactionMock,
      updateRecurringTransactionMock,
      deactivateRecurringTransactionMock,
      deleteRecurringTransactionMock,
      getDashboardSummaryMock,
      getDashboardChartsMock,
      getAiSummaryMock,
      getBudgetAdviceMock,
      getExpensesMock
    ]) {
      mockFn.mockClear()
    }
  })

  function mountPage() {
    return mount(RecurringTransactions, {
      global: { plugins: [createPinia(), createI18nInstance()] }
    })
  }

  it('renders schedule and current month occurrences', async () => {
    const wrapper = mountPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Recurring Schedule')
      expect(wrapper.text()).toContain('2026-07-15')
      expect(wrapper.text()).toContain('This Month')
      expect(wrapper.text()).toContain('Expense #77')
    })
  })

  it('generates the current month and refreshes dashboard and expenses', async () => {
    const wrapper = mountPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Generate This Month')
    })

    await wrapper.find('button.btn.btn-primary').trigger('click')

    await vi.waitFor(() => {
      expect(generateCurrentMonthRecurringTransactionsMock).toHaveBeenCalled()
      expect(getDashboardSummaryMock).toHaveBeenCalled()
      expect(getExpensesMock).toHaveBeenCalled()
      expect(wrapper.text()).toContain('Created 1, skipped 0, existing 1.')
    })
  })

  it('generates and skips a single pending occurrence', async () => {
    const wrapper = mountPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Mark as Paid')
    })

    const markPaidButton = wrapper.findAll('button').find(button => button.text() === 'Mark as Paid')
    await markPaidButton.trigger('click')

    expect(generateRecurringOccurrenceMock).toHaveBeenCalledWith(11)
  })

  it('skips a single pending occurrence', async () => {
    const wrapper = mountPage()

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Skip')
    })

    const skipButton = wrapper.findAll('button').find(button => button.text() === 'Skip')
    await skipButton.trigger('click')

    expect(skipRecurringOccurrenceMock).toHaveBeenCalledWith(11)
  })

  it('creates through the store flow', async () => {
    const wrapper = mountPage()

    await wrapper.find('#recurring-amount').setValue('99')
    await wrapper.find('#recurring-type').setValue('expense')
    await wrapper.find('#recurring-category').setValue('Food')
    await wrapper.find('#recurring-frequency').setValue('weekly')
    await wrapper.find('#recurring-start').setValue('2026-07-10')
    await wrapper.find('form.form-row').trigger('submit')

    await vi.waitFor(() => {
      expect(createRecurringTransactionMock).toHaveBeenCalled()
    })

  })
})
