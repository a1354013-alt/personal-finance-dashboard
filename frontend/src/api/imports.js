import api from './index'

export function previewTransactionImport(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/imports/transactions/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function confirmTransactionImport(batchId, selectedRows) {
  return api.post(`/imports/transactions/${batchId}/confirm`, {
    selected_row_numbers: Array.isArray(selectedRows) ? selectedRows : null
  })
}

export function listTransactionImports() {
  return api.get('/imports/transactions')
}

export function getTransactionImport(batchId) {
  return api.get(`/imports/transactions/${batchId}`)
}
