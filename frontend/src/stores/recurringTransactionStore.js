import { ref } from 'vue'
import { defineStore } from 'pinia'
import {
  createRecurringTransaction,
  deactivateRecurringTransaction,
  deleteRecurringTransaction,
  getRecurringTransactions,
  updateRecurringTransaction
} from '@/api/recurringTransactions'
import { normalizeRecurringTransaction } from '@/api/contracts'
import i18n from '@/i18n'
import { toErrorMessage } from '@/stores/storeUtils'

export const useRecurringTransactionStore = defineStore('recurringTransaction', () => {
  const items = ref([])
  const loading = ref(false)
  const submitting = ref(false)
  const deleting = ref(false)
  const error = ref(null)

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

  async function saveItem(data, id = null) {
    submitting.value = true
    error.value = null
    try {
      if (id) {
        await updateRecurringTransaction(id, data)
      } else {
        await createRecurringTransaction(data)
      }
      await fetchItems()
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
      await fetchItems()
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
      await fetchItems()
    } catch (e) {
      error.value = toErrorMessage(e, i18n.global.t('common.unknownError'))
      throw e
    } finally {
      deleting.value = false
    }
  }

  return {
    items,
    loading,
    submitting,
    deleting,
    error,
    fetchItems,
    saveItem,
    deactivateItem,
    removeItem
  }
})
