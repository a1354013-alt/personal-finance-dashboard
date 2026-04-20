import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createBudget, deleteBudget, getBudgets } from '@/api/budgets'

export const useBudgetStore = defineStore('budget', () => {
  const budgets = ref([])
  const loading = ref(false)
  const submitting = ref(false)
  const error = ref(null)

  function normalizeBudget(row) {
    if (!row || typeof row !== 'object') return null
    return {
      id: Number(row.id),
      user_id: Number(row.user_id),
      category: String(row.category || ''),
      monthly_limit: Number(row.monthly_limit ?? 0),
      current_spent: Number(row.current_spent ?? 0),
      percent_used: Number(row.percent_used ?? 0),
      over_budget: Boolean(row.over_budget),
      created_at: row.created_at || null
    }
  }

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
      if (saved) {
        const index = budgets.value.findIndex((b) => b.id === saved.id)
        if (index >= 0) budgets.value.splice(index, 1, saved)
        else budgets.value = [...budgets.value, saved].sort((a, b) => a.category.localeCompare(b.category))
      } else {
        await fetchBudgets()
      }
      return saved
    } catch (e) {
      error.value = e.message || 'Unable to save budget.'
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function removeBudget(id) {
    error.value = null
    try {
      await deleteBudget(id)
      budgets.value = budgets.value.filter((b) => b.id !== id)
    } catch (e) {
      error.value = e.message || 'Unable to delete budget.'
      throw e
    }
  }

  return {
    budgets,
    loading,
    submitting,
    error,
    normalizeBudget,
    fetchBudgets,
    saveBudget,
    removeBudget
  }
})

