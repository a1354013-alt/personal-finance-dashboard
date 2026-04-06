import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getExpenses, createExpense, deleteExpense } from '@/api/expenses'

export const useExpenseStore = defineStore('expense', () => {
  const expenses = ref([])
  const loading = ref(false)
  const submitting = ref(false)
  const error = ref(null)

  // 計算總收入
  const totalIncome = computed(() =>
    expenses.value
      .filter(e => e.type === 'income')
      .reduce((sum, e) => sum + e.amount, 0)
  )

  // 計算總支出
  const totalExpense = computed(() =>
    expenses.value
      .filter(e => e.type === 'expense')
      .reduce((sum, e) => sum + e.amount, 0)
  )

  async function fetchExpenses(params = {}) {
    loading.value = true
    error.value = null
    try {
      expenses.value = await getExpenses(params)
    } catch (e) {
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
    error.value = null
    try {
      await deleteExpense(id)
      expenses.value = expenses.value.filter(e => e.id !== id)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  return {
    expenses, loading, submitting, error,
    totalIncome, totalExpense,
    fetchExpenses, addExpense, removeExpense,
  }
})
