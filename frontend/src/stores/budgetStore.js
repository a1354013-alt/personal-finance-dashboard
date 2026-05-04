import { defineStore } from 'pinia'
import { ref } from 'vue'
import { deleteBudget, getBudgets, getBudgetSummary, updateBudget, upsertBudget } from '@/api/budgets'
import { normalizeBudget, normalizeBudgetSummary } from '@/api/contracts'
import i18n from '@/i18n'
import { toErrorMessage } from '@/stores/storeUtils'

export const useBudgetStore = defineStore('budget', () => {
  const budgets = ref([])
  const summary = ref(null)
  const loading = ref(false)
  const summaryLoading = ref(false)
  const submitting = ref(false)
  const deleting = ref(false)
  const error = ref(null)
  const selectedMonth = ref(new Date().toISOString().slice(0, 7))

  async function fetchBudgets() {
    loading.value = true
    error.value = null
    try {
      const result = await getBudgets(selectedMonth.value)
      budgets.value = Array.isArray(result) ? result.map(normalizeBudget).filter(Boolean) : []
    } catch (e) {
      budgets.value = []
      error.value = toErrorMessage(e, i18n.global.t('budgets.loading'))
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary() {
    summaryLoading.value = true
    error.value = null
    try {
      const result = await getBudgetSummary(selectedMonth.value)
      summary.value = normalizeBudgetSummary(result)
    } catch (e) {
      summary.value = null
      error.value = toErrorMessage(e, i18n.global.t('budgets.loading'))
    } finally {
      summaryLoading.value = false
    }
  }

  async function saveBudget(payload) {
    submitting.value = true
    error.value = null
    try {
      // Ensure month is included
      const data = { month: selectedMonth.value, ...payload }
      const saved = normalizeBudget(await upsertBudget(data))
      await Promise.all([fetchBudgets(), fetchSummary()])
      return saved
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function modifyBudget(id, payload) {
    submitting.value = true
    error.value = null
    try {
      const saved = normalizeBudget(await updateBudget(id, payload))
      await Promise.all([fetchBudgets(), fetchSummary()])
      return saved
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
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
      await Promise.all([fetchBudgets(), fetchSummary()])
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
      throw e
    } finally {
      deleting.value = false
    }
  }

  function setSelectedMonth(month) {
    selectedMonth.value = month
    return Promise.all([fetchBudgets(), fetchSummary()])
  }

  return {
    budgets,
    summary,
    loading,
    summaryLoading,
    submitting,
    deleting,
    error,
    selectedMonth,
    fetchBudgets,
    fetchSummary,
    saveBudget,
    modifyBudget,
    removeBudget,
    setSelectedMonth
  }
})
