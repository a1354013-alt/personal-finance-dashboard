<template>
  <div>
    <div class="page-header">
      <h1>{{ t('recurring.title') }}</h1>
      <p>{{ t('recurring.subtitle') }}</p>
    </div>

    <section class="card">
      <div class="section-heading">
        <div>
          <h2>{{ t('recurring.automationTitle') }}</h2>
          <p>{{ t('recurring.automationSubtitle') }}</p>
        </div>
        <button class="btn btn-primary" :disabled="store.generating" @click="handleGenerateMonth">
          {{ store.generating ? t('recurring.generating') : t('recurring.generateMonthAction') }}
        </button>
      </div>

      <div v-if="store.generationSummary" class="success-msg">
        {{ generationSummaryText }}
      </div>
      <div v-if="store.error" class="error-msg">{{ store.error }}</div>

      <div v-if="store.loadingOccurrences" class="loading-text">{{ t('recurring.loadingOccurrences') }}</div>
      <div v-else-if="!store.occurrences.length" class="empty-state">{{ t('recurring.emptyOccurrences') }}</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>{{ t('common.date') }}</th>
            <th>{{ t('common.type') }}</th>
            <th>{{ t('common.category') }}</th>
            <th>{{ t('common.amount') }}</th>
            <th>{{ t('recurring.occurrenceStatus') }}</th>
            <th>{{ t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="occurrence in store.occurrences" :key="occurrence.id || `${occurrence.recurring_transaction_id}-${occurrence.scheduled_date}`">
            <td>{{ occurrence.scheduled_date }}</td>
            <td>{{ occurrence.recurring_transaction?.type === 'income' ? t('expenses.typeIncome') : t('expenses.typeExpense') }}</td>
            <td>{{ translateCategory(t, occurrence.recurring_transaction?.category || '') }}</td>
            <td :class="occurrence.recurring_transaction?.type === 'income' ? 'amount-income' : 'amount-expense'">
              {{ formatCurrency(occurrence.recurring_transaction?.amount || 0) }}
            </td>
            <td>
              <span class="badge" :class="occurrenceBadgeClass(occurrence.status)">
                {{ t(`recurring.statuses.${occurrence.status}`) }}
              </span>
            </td>
            <td class="action-cell">
              <button
                v-if="occurrence.status === 'pending' && occurrence.id"
                class="btn btn-secondary"
                :disabled="store.generating"
                @click="handleGenerateOccurrence(occurrence.id)"
              >
                {{ t('recurring.markPaidAction') }}
              </button>
              <button
                v-if="occurrence.status === 'pending' && occurrence.id"
                class="btn btn-secondary"
                :disabled="store.generating"
                @click="handleSkipOccurrence(occurrence.id)"
              >
                {{ t('recurring.skipOccurrenceAction') }}
              </button>
              <span v-if="occurrence.generated_expense_id" class="helper-inline">
                {{ t('recurring.generatedExpense', { id: occurrence.generated_expense_id }) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="card">
      <h2>{{ editingId ? t('recurring.editTitle') : t('recurring.formTitle') }}</h2>
      <div v-if="formError" class="error-msg">{{ formError }}</div>

      <form class="form-row" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="recurring-amount">{{ t('common.amount') }}</label>
          <input id="recurring-amount" v-model.number="form.amount" type="number" min="0.01" step="0.01">
        </div>
        <div class="form-group">
          <label for="recurring-type">{{ t('common.type') }}</label>
          <select id="recurring-type" v-model="form.type" @change="form.category = ''">
            <option value="expense">{{ t('expenses.typeExpense') }}</option>
            <option value="income">{{ t('expenses.typeIncome') }}</option>
          </select>
        </div>
        <div class="form-group">
          <label for="recurring-category">{{ t('common.category') }}</label>
          <select id="recurring-category" v-model="form.category">
            <option value="" disabled>{{ t('expenses.selectCategory') }}</option>
            <option v-for="category in activeCategories" :key="category" :value="category">{{ translateCategory(t, category) }}</option>
          </select>
        </div>
        <div class="form-group">
          <label for="recurring-frequency">{{ t('recurring.frequency') }}</label>
          <select id="recurring-frequency" v-model="form.frequency">
            <option value="weekly">{{ t('recurring.frequencies.weekly') }}</option>
            <option value="monthly">{{ t('recurring.frequencies.monthly') }}</option>
            <option value="yearly">{{ t('recurring.frequencies.yearly') }}</option>
          </select>
        </div>
        <div class="form-group">
          <label for="recurring-start">{{ t('recurring.startDate') }}</label>
          <input id="recurring-start" v-model="form.start_date" type="date">
        </div>
        <div class="form-group">
          <label for="recurring-end">{{ t('recurring.endDate') }}</label>
          <input id="recurring-end" v-model="form.end_date" type="date">
        </div>
        <div class="form-group note-group">
          <label for="recurring-note">{{ t('common.note') }}</label>
          <input id="recurring-note" v-model.trim="form.note" type="text">
        </div>
        <button class="btn btn-primary" :disabled="store.submitting">
          {{ store.submitting ? t('recurring.saving') : (editingId ? t('recurring.updateAction') : t('recurring.createAction')) }}
        </button>
        <button v-if="editingId" type="button" class="btn btn-secondary" @click="resetForm">
          {{ t('common.cancel') }}
        </button>
      </form>
    </section>

    <section class="card">
      <h2>{{ t('recurring.listTitle') }}</h2>
      <div v-if="store.loading" class="loading-text">{{ t('recurring.loading') }}</div>
      <div v-else-if="!store.items.length" class="empty-state">{{ t('recurring.empty') }}</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>{{ t('common.type') }}</th>
            <th>{{ t('common.category') }}</th>
            <th>{{ t('common.amount') }}</th>
            <th>{{ t('recurring.frequency') }}</th>
            <th>{{ t('recurring.nextRunDate') }}</th>
            <th>{{ t('recurring.status') }}</th>
            <th>{{ t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in store.items" :key="item.id">
            <td>{{ item.type === 'income' ? t('expenses.typeIncome') : t('expenses.typeExpense') }}</td>
            <td>{{ translateCategory(t, item.category) }}</td>
            <td :class="item.type === 'income' ? 'amount-income' : 'amount-expense'">{{ formatCurrency(item.amount) }}</td>
            <td>{{ t(`recurring.frequencies.${item.frequency}`) }}</td>
            <td>{{ item.next_run_date || '-' }}</td>
            <td>
              <span class="badge" :class="item.is_active ? 'badge-success' : 'badge-warning'">
                {{ item.is_active ? t('recurring.active') : t('recurring.inactive') }}
              </span>
            </td>
            <td class="action-cell">
              <button class="btn btn-secondary" @click="startEdit(item)">{{ t('common.edit') }}</button>
              <button v-if="item.is_active" class="btn btn-secondary" :disabled="store.submitting" @click="store.deactivateItem(item.id)">
                {{ t('recurring.deactivate') }}
              </button>
              <button class="btn btn-danger" :disabled="store.deleting" @click="store.removeItem(item.id)">
                {{ t('common.delete') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { EXPENSE_CATEGORIES, INCOME_CATEGORIES } from '@/constants/categories'
import { useRecurringTransactionStore } from '@/stores/recurringTransactionStore'
import { useDashboardStore } from '@/stores/dashboardStore'
import { useExpenseStore } from '@/stores/expenseStore'
import { translateCategory } from '@/utils/categories'
import { getLocalDate } from '@/utils/date'
import { formatCurrency as formatCurrencyValue } from '@/utils/formatters'

const store = useRecurringTransactionStore()
const dashboardStore = useDashboardStore()
const expenseStore = useExpenseStore()
const { t, locale } = useI18n()
const formError = ref('')
const editingId = ref(null)
const today = getLocalDate()
const form = ref(defaultForm())

const activeCategories = computed(() => (form.value.type === 'income' ? INCOME_CATEGORIES : EXPENSE_CATEGORIES))
const generationSummaryText = computed(() => {
  if (!store.generationSummary) return ''
  return t('recurring.generationSummary', {
    created: store.generationSummary.created_count,
    skipped: store.generationSummary.skipped_count,
    existing: store.generationSummary.already_existing_count
  })
})

onMounted(() => {
  store.refreshAll()
})

function defaultForm() {
  return {
    amount: null,
    type: 'expense',
    category: '',
    note: '',
    frequency: 'monthly',
    start_date: today,
    end_date: '',
    is_active: true
  }
}

function formatCurrency(value) {
  return formatCurrencyValue(value, locale.value)
}

function validateForm() {
  if (!form.value.amount || form.value.amount <= 0) return t('expenses.amountError')
  if (!form.value.category) return t('expenses.categoryError')
  if (!form.value.start_date) return t('recurring.startDateError')
  if (form.value.end_date && form.value.end_date < form.value.start_date) return t('recurring.endDateError')
  return ''
}

async function handleSubmit() {
  formError.value = validateForm()
  if (formError.value) return

  const payload = {
    ...form.value,
    end_date: form.value.end_date || null
  }

  try {
    await store.saveItem(payload, editingId.value)
    resetForm()
  } catch (_error) {
    // Store error is already displayed.
  }
}

async function refreshDependentViews() {
  await Promise.allSettled([
    dashboardStore.fetchSummary(),
    expenseStore.fetchExpenses()
  ])
}

async function handleGenerateMonth() {
  try {
    await store.generateMonth()
    await refreshDependentViews()
  } catch (_error) {
    // Store error is already displayed.
  }
}

async function handleGenerateOccurrence(id) {
  try {
    await store.generateOccurrenceItem(id)
    await refreshDependentViews()
  } catch (_error) {
    // Store error is already displayed.
  }
}

async function handleSkipOccurrence(id) {
  try {
    await store.skipOccurrenceItem(id)
    await refreshDependentViews()
  } catch (_error) {
    // Store error is already displayed.
  }
}

function occurrenceBadgeClass(status) {
  if (status === 'generated') return 'badge-success'
  if (status === 'skipped') return 'badge-warning'
  return 'badge-secondary'
}

function startEdit(item) {
  editingId.value = item.id
  form.value = {
    amount: item.amount,
    type: item.type,
    category: item.category,
    note: item.note || '',
    frequency: item.frequency,
    start_date: item.start_date,
    end_date: item.end_date || '',
    is_active: item.is_active
  }
}

function resetForm() {
  editingId.value = null
  formError.value = ''
  form.value = defaultForm()
}
</script>

<style scoped>
.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.section-heading p {
  margin: 6px 0 0;
  color: var(--text-muted);
}

.note-group {
  min-width: 240px;
}

.action-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.helper-inline {
  color: var(--text-muted);
  font-size: 13px;
}

.amount-income {
  color: #1f8f5f;
  font-weight: 700;
}

.amount-expense {
  color: #d04d48;
  font-weight: 700;
}

@media (max-width: 720px) {
  .section-heading {
    flex-direction: column;
  }
}
</style>
