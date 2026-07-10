import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { createExpense, deleteExpense, getExpenses, updateExpense } from '@/api/expenses'
import { normalizeExpense } from '@/api/contracts'
import i18n from '@/i18n'
import { toErrorMessage } from '@/stores/storeUtils'

export const useExpenseStore = defineStore('expense', () => {
  const expenses = ref([])
  const loading = ref(false)
  const submitting = ref(false)
  const deleting = ref(false)
  const error = ref(null)
  const lastParams = ref({})

  const totalIncome = computed(() =>
    expenses.value
      .filter((expense) => expense.type === 'income')
      .reduce((sum, expense) => sum + expense.amount, 0)
  )

  const totalExpense = computed(() =>
    expenses.value
      .filter((expense) => expense.type === 'expense')
      .reduce((sum, expense) => sum + expense.amount, 0)
  )

  async function fetchExpenses(params = {}) {
    const normalizedParams = { ...params }
    loading.value = true
    error.value = null
    lastParams.value = normalizedParams
    try {
      const result = await getExpenses(normalizedParams)
      expenses.value = Array.isArray(result) ? result.map(normalizeExpense).filter(Boolean) : []
    } catch (e) {
      expenses.value = []
      error.value = toErrorMessage(e, i18n.global.t('expenses.loading'))
    } finally {
      loading.value = false
    }
  }

  async function addExpense(data, options = {}) {
    const refreshParams = options.refreshParams ? { ...options.refreshParams } : { ...lastParams.value }
    submitting.value = true
    error.value = null
    try {
      await createExpense(data)
      await fetchExpenses(refreshParams)
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function editExpense(id, data, options = {}) {
    const refreshParams = options.refreshParams ? { ...options.refreshParams } : { ...lastParams.value }
    submitting.value = true
    error.value = null
    try {
      await updateExpense(id, data)
      await fetchExpenses(refreshParams)
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function removeExpense(id) {
    if (deleting.value) return
    error.value = null
    try {
      deleting.value = true
      await deleteExpense(id)
      await fetchExpenses(lastParams.value)
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
      throw e
    } finally {
      deleting.value = false
    }
  }

  return {
    expenses,
    loading,
    submitting,
    deleting,
    error,
    totalIncome,
    totalExpense,
    fetchExpenses,
    addExpense,
    editExpense,
    removeExpense
  }
})
