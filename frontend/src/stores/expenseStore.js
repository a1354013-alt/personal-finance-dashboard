import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { createExpense, deleteExpense, getExpenses } from '@/api/expenses'
import { normalizeExpense } from '@/api/contracts'

export const useExpenseStore = defineStore('expense', () => {
  const expenses = ref([])
  const loading = ref(false)
  const submitting = ref(false)
  const deleting = ref(false)
  const error = ref(null)

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
    loading.value = true
    error.value = null
    try {
      const result = await getExpenses(params)
      expenses.value = Array.isArray(result) ? result.map(normalizeExpense).filter(Boolean) : []
    } catch (e) {
      expenses.value = []
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function addExpense(data) {
    submitting.value = true
    error.value = null
    try {
      await createExpense(data)
      await fetchExpenses()
    } catch (e) {
      error.value = e.message
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
      expenses.value = expenses.value.filter((expense) => expense.id !== Number(id))
    } catch (e) {
      error.value = e.message
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
    removeExpense
  }
})
