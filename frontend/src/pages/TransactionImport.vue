<template>
  <div class="transaction-import-page">
    <div class="page-header">
      <h1>{{ t('imports.title') }}</h1>
      <p>{{ t('imports.subtitle') }}</p>
    </div>

    <section class="card upload-card">
      <div class="upload-copy">
        <h2>{{ t('imports.uploadTitle') }}</h2>
        <p>{{ t('imports.uploadHint') }}</p>
      </div>

      <div v-if="store.error" class="error-msg">{{ store.error }}</div>
      <div v-if="successMessage" class="success-msg">{{ successMessage }}</div>

      <div class="form-row upload-row">
        <div class="form-group file-group">
          <label for="transaction-import-file">{{ t('imports.fileLabel') }}</label>
          <input
            id="transaction-import-file"
            type="file"
            accept=".csv,.xlsx"
            @change="handleFileChange"
          />
        </div>

        <button class="btn btn-primary" :disabled="!selectedFile || store.status === 'uploading'" @click="handlePreview">
          {{ store.status === 'uploading' ? t('imports.uploading') : t('imports.previewAction') }}
        </button>
      </div>

      <p class="helper-text">
        {{ t('imports.supportedFormats') }}
        <a href="/demo/sample-transactions.csv" target="_blank" rel="noreferrer">{{ t('imports.sampleFile') }}</a>
      </p>
    </section>

    <section v-if="store.preview" class="card summary-card">
      <div class="section-heading">
        <div>
          <h2>{{ t('imports.previewTitle') }}</h2>
          <p>{{ store.preview.batch.file_name }}</p>
        </div>
        <button class="btn btn-success" :disabled="confirmDisabled" @click="handleConfirm">
          {{ store.status === 'importing' ? t('imports.importing') : t('imports.confirmAction') }}
        </button>
      </div>

      <div class="summary-grid">
        <article v-for="card in summaryCards" :key="card.label" class="summary-pill">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </div>

      <div class="selection-row">
        <label class="selection-toggle">
          <input
            type="checkbox"
            :checked="allValidSelected"
            :disabled="validRowNumbers.length === 0"
            @change="toggleAllValidRows"
          />
          <span>{{ t('imports.selectAllValid') }}</span>
        </label>
      </div>

      <div class="table-wrap">
        <table class="table import-table">
          <thead>
            <tr>
              <th>{{ t('imports.columns.include') }}</th>
              <th>#</th>
              <th>{{ t('common.date') }}</th>
              <th>{{ t('common.type') }}</th>
              <th>{{ t('common.category') }}</th>
              <th>{{ t('common.amount') }}</th>
              <th>{{ t('common.note') }}</th>
              <th>{{ t('imports.columns.status') }}</th>
              <th>{{ t('imports.columns.details') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in store.preview.rows" :key="row.id">
              <td>
                <input
                  type="checkbox"
                  :checked="selectedRows.includes(row.source_row_number)"
                  :disabled="row.status !== 'valid'"
                  @change="toggleRow(row.source_row_number)"
                />
              </td>
              <td>{{ row.source_row_number }}</td>
              <td>{{ row.normalized.transaction_date || '-' }}</td>
              <td>{{ row.normalized.type || '-' }}</td>
              <td>{{ row.normalized.category || '-' }}</td>
              <td>{{ row.normalized.amount == null ? '-' : formatCurrency(row.normalized.amount) }}</td>
              <td>{{ row.normalized.description || '-' }}</td>
              <td>
                <span class="badge" :class="statusBadgeClass(row.status)">
                  {{ t(`imports.status.${row.status}`) }}
                </span>
              </td>
              <td class="details-cell">
                <span v-if="row.validation_errors.length">{{ row.validation_errors.join(' ') }}</span>
                <span v-else-if="row.duplicate_reasons.length">{{ row.duplicate_reasons.join(', ') }}</span>
                <span v-else-if="row.warnings.length">{{ row.warnings.join(' ') }}</span>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card history-card">
      <div class="section-heading">
        <div>
          <h2>{{ t('imports.historyTitle') }}</h2>
          <p>{{ t('imports.historySubtitle') }}</p>
        </div>
      </div>

      <div v-if="store.loadingHistory" class="loading-text">{{ t('common.loading') }}</div>
      <div v-else-if="store.history.length === 0" class="empty-state">{{ t('imports.emptyHistory') }}</div>
      <div v-else class="history-list">
        <article v-for="batch in store.history" :key="batch.id" class="history-item">
          <div>
            <strong>{{ batch.file_name }}</strong>
            <p>{{ batch.status }} · {{ batch.summary.rows_to_import }} {{ t('imports.readyRows') }}</p>
          </div>
          <span>{{ batch.created_at || '' }}</span>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTransactionImportStore } from '@/stores/transactionImportStore'
import { formatCurrency as formatCurrencyValue } from '@/utils/formatters'

const store = useTransactionImportStore()
const selectedFile = ref(null)
const selectedRows = ref([])
const { t, locale } = useI18n()

const summaryCards = computed(() => {
  const summary = store.preview?.batch?.summary
  if (!summary) return []
  return [
    { label: t('imports.summary.totalRows'), value: summary.total_rows },
    { label: t('imports.summary.validRows'), value: summary.valid_rows },
    { label: t('imports.summary.invalidRows'), value: summary.invalid_rows },
    { label: t('imports.summary.duplicateRows'), value: summary.duplicate_rows },
    { label: t('imports.summary.rowsToImport'), value: selectedRows.value.length }
  ]
})

const validRowNumbers = computed(() => store.validRows.map(row => row.source_row_number))
const allValidSelected = computed(() => validRowNumbers.value.length > 0 && validRowNumbers.value.every(number => selectedRows.value.includes(number)))
const confirmDisabled = computed(() => !store.preview?.batch?.id || selectedRows.value.length === 0 || store.status === 'importing')
const successMessage = computed(() => {
  if (!store.result) return ''
  return t('imports.importResult', {
    created: store.result.created_count,
    skipped: store.result.skipped_count
  })
})

watch(
  () => store.preview?.batch?.id,
  () => {
    selectedRows.value = validRowNumbers.value.slice()
  }
)

onMounted(() => {
  store.fetchHistory()
})

function formatCurrency(value) {
  return formatCurrencyValue(value, locale.value)
}

function handleFileChange(event) {
  selectedFile.value = event.target.files?.[0] ?? null
}

async function handlePreview() {
  if (!selectedFile.value) return
  try {
    await store.uploadFile(selectedFile.value)
  } catch (_error) {
    // Store error is already shown in the page.
  }
}

async function handleConfirm() {
  if (!store.preview?.batch?.id) return
  try {
    await store.confirm(store.preview.batch.id, selectedRows.value)
  } catch (_error) {
    // Store error is already shown in the page.
  }
}

function toggleRow(rowNumber) {
  if (selectedRows.value.includes(rowNumber)) {
    selectedRows.value = selectedRows.value.filter(item => item !== rowNumber)
    return
  }
  selectedRows.value = [...selectedRows.value, rowNumber].sort((a, b) => a - b)
}

function toggleAllValidRows() {
  selectedRows.value = allValidSelected.value ? [] : validRowNumbers.value.slice()
}

function statusBadgeClass(status) {
  if (status === 'valid') return 'badge-success'
  if (status === 'duplicate') return 'badge-warning'
  return 'badge-danger'
}
</script>

<style scoped>
.transaction-import-page {
  display: grid;
  gap: 20px;
}

.upload-card,
.summary-card,
.history-card {
  display: grid;
  gap: 18px;
}

.upload-copy p,
.section-heading p,
.helper-text {
  margin: 6px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.file-group {
  min-width: 280px;
}

.helper-text a {
  font-weight: 700;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 14px;
}

.summary-pill {
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(236, 244, 247, 0.9), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(199, 214, 222, 0.66);
}

.summary-pill span {
  display: block;
  color: var(--text-muted);
  font-size: 13px;
}

.summary-pill strong {
  display: block;
  margin-top: 8px;
  font-size: 26px;
}

.selection-row {
  display: flex;
  justify-content: flex-end;
}

.selection-toggle {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.table-wrap {
  overflow-x: auto;
}

.import-table {
  min-width: 880px;
}

.details-cell {
  color: var(--text-muted);
  min-width: 220px;
}

.history-list {
  display: grid;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(215, 226, 234, 0.82);
  background: rgba(249, 252, 253, 0.82);
}

.history-item p {
  margin: 4px 0 0;
  color: var(--text-muted);
}

@media (max-width: 720px) {
  .section-heading {
    flex-direction: column;
  }

  .selection-row {
    justify-content: flex-start;
  }
}
</style>
