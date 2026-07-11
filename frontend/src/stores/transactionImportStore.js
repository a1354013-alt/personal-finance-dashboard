import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  confirmTransactionImport,
  getTransactionImport,
  listTransactionImports,
  previewTransactionImport
} from '@/api/imports'
import {
  normalizeTransactionImportBatch,
  normalizeTransactionImportConfirmResult,
  normalizeTransactionImportPreview
} from '@/api/contracts'
import i18n from '@/i18n'
import { toErrorMessage } from '@/stores/storeUtils'

export const useTransactionImportStore = defineStore('transactionImport', () => {
  const status = ref('idle')
  const preview = ref(null)
  const history = ref([])
  const result = ref(null)
  const loadingHistory = ref(false)
  const error = ref('')
  const mapping = ref({})

  const hasPreview = computed(() => Boolean(preview.value?.batch?.id))
  const validRows = computed(() => preview.value?.rows?.filter(row => row.status === 'valid') ?? [])

  async function fetchHistory() {
    loadingHistory.value = true
    try {
      const payload = await listTransactionImports()
      history.value = Array.isArray(payload) ? payload.map(normalizeTransactionImportBatch).filter(Boolean) : []
    } catch (_error) {
      history.value = []
    } finally {
      loadingHistory.value = false
    }
  }

  async function uploadFile(file, columnMapping = null) {
    status.value = 'uploading'
    error.value = ''
    result.value = null
    try {
      const payload = await previewTransactionImport(file, columnMapping)
      preview.value = normalizeTransactionImportPreview(payload)
      mapping.value = preview.value?.applied_mapping ?? {}
      status.value = 'preview_ready'
      await fetchHistory()
      return preview.value
    } catch (e) {
      preview.value = null
      status.value = 'error'
      error.value = toErrorMessage(e, i18n.global.t('imports.errors.preview'))
      throw e
    }
  }

  async function confirm(batchId, selectedRows) {
    status.value = 'importing'
    error.value = ''
    try {
      const payload = await confirmTransactionImport(batchId, selectedRows)
      result.value = normalizeTransactionImportConfirmResult(payload)
      status.value = 'imported'
      if (preview.value?.batch?.id === batchId) {
        preview.value = normalizeTransactionImportPreview(await getTransactionImport(batchId))
      }
      await fetchHistory()
      return result.value
    } catch (e) {
      status.value = 'error'
      error.value = toErrorMessage(e, i18n.global.t('imports.errors.confirm'))
      throw e
    }
  }

  return {
    status,
    preview,
    mapping,
    history,
    result,
    loadingHistory,
    error,
    hasPreview,
    validRows,
    fetchHistory,
    uploadFile,
    confirm
  }
})
