import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createBudget, deleteBudget, getBudgets } from '@/api/budgets'
import { normalizeBudget } from '@/api/contracts'

export const useBudgetStore = defineStore('budget', () => {
  const budgets = ref([])
  const loading = ref(false)
  const submitting = ref(false)
  const deleting = ref(false)
  const error = ref(null)

  async function fetchBudgets() {
    loading.value = true
    error.value = null
    try {
      const result = await getBudgets()
      budgets.value = Array.isArray(result) ? result.map(normalizeBudget).filter(Boolean) : []
    } catch (e) {
      budgets.value = []
      error.value = e.message || 'Unable to load budgets.'
    } finally {
      loading.value = false
    }
  }

  async function saveBudget(payload) {
    submitting.value = true
    error.value = null
    try {
      const saved = normalizeBudget(await createBudget(payload))
      await fetchBudgets()
      return saved
    } catch (e) {
      error.value = e.message || 'Unable to save budget.'
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function removeBudget(id) {
    if (deleting.value) return
    error.value = null
    try {
      deleting.value = true
      await deleteBudget(id)
      await fetchBudgets()
    } catch (e) {
      error.value = e.message || 'Unable to delete budget.'
      throw e
    } finally {
      deleting.value = false
    }
  }

  return {
    budgets,
    loading,
    submitting,
    deleting,
    error,
    normalizeBudget,
    fetchBudgets,
    saveBudget,
    removeBudget
  }
})

