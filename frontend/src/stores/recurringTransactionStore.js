import { ref } from 'vue'
import { defineStore } from 'pinia'
import {
  createRecurringTransaction,
  deactivateRecurringTransaction,
  deleteRecurringTransaction,
  generateCurrentMonthRecurringTransactions,
  generateRecurringOccurrence,
  getRecurringOccurrences,
  getRecurringTransactions,
  skipRecurringOccurrence,
  updateRecurringTransaction
} from '@/api/recurringTransactions'
import {
  normalizeRecurringGenerationSummary,
  normalizeRecurringOccurrence,
  normalizeRecurringTransaction
} from '@/api/contracts'
import i18n from '@/i18n'
import { toErrorMessage } from '@/stores/storeUtils'

export const useRecurringTransactionStore = defineStore('recurringTransaction', () => {
  const items = ref([])
  const occurrences = ref([])
  const loading = ref(false)
  const loadingOccurrences = ref(false)
  const submitting = ref(false)
  const deleting = ref(false)
  const generating = ref(false)
  const error = ref(null)
  const generationSummary = ref(null)

  async function fetchItems() {
    loading.value = true
    error.value = null
    try {
      const result = await getRecurringTransactions()
      items.value = Array.isArray(result) ? result.map(normalizeRecurringTransaction).filter(Boolean) : []
    } catch (e) {
      items.value = []
      error.value = toErrorMessage(e, i18n.global.t('recurring.errors.load'))
    } finally {
      loading.value = false
    }
  }

  async function fetchOccurrences(month = null) {
    loadingOccurrences.value = true
    error.value = null
    try {
      const result = await getRecurringOccurrences(month)
      occurrences.value = Array.isArray(result) ? result.map(normalizeRecurringOccurrence).filter(Boolean) : []
    } catch (e) {
      occurrences.value = []
      error.value = toErrorMessage(e, i18n.global.t('recurring.errors.occurrences'))
      throw e
    } finally {
      loadingOccurrences.value = false
    }
  }

  async function refreshAll() {
    await fetchItems()
    await fetchOccurrences()
  }

  async function saveItem(data, id = null) {
    submitting.value = true
    error.value = null
    try {
      if (id) {
        await updateRecurringTransaction(id, data)
      } else {
        await createRecurringTransaction(data)
      }
      await refreshAll()
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function deactivateItem(id) {
    submitting.value = true
    error.value = null
    try {
      await deactivateRecurringTransaction(id)
      await refreshAll()
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function removeItem(id) {
    deleting.value = true
    error.value = null
    try {
      await deleteRecurringTransaction(id)
      await refreshAll()
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
      throw e
    } finally {
      deleting.value = false
    }
  }

  async function generateMonth() {
    generating.value = true
    error.value = null
    try {
      const result = await generateCurrentMonthRecurringTransactions()
      generationSummary.value = normalizeRecurringGenerationSummary(result)
      await refreshAll()
      return generationSummary.value
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('recurring.errors.generate'))
      throw e
    } finally {
      generating.value = false
    }
  }

  async function generateOccurrenceItem(id) {
    generating.value = true
    error.value = null
    try {
      const result = await generateRecurringOccurrence(id)
      generationSummary.value = normalizeRecurringGenerationSummary(result?.summary)
      await refreshAll()
      return result
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('recurring.errors.generate'))
      throw e
    } finally {
      generating.value = false
    }
  }

  async function skipOccurrenceItem(id) {
    generating.value = true
    error.value = null
    try {
      const result = await skipRecurringOccurrence(id)
      generationSummary.value = normalizeRecurringGenerationSummary(result?.summary)
      await refreshAll()
      return result
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('recurring.errors.skip'))
      throw e
    } finally {
      generating.value = false
    }
  }

  return {
    items,
    occurrences,
    loading,
    loadingOccurrences,
    submitting,
    deleting,
    generating,
    error,
    generationSummary,
    fetchItems,
    fetchOccurrences,
    refreshAll,
    saveItem,
    deactivateItem,
    removeItem,
    generateMonth,
    generateOccurrenceItem,
    skipOccurrenceItem
  }
})
