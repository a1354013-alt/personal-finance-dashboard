<template>
  <div class="budgets-page">
    <div class="page-header">
      <div class="header-content">
        <h1>{{ t('budgets.title') }}</h1>
        <p>{{ t('budgets.subtitle') }}</p>
      </div>
      <div class="month-selector">
        <input
          v-model="store.selectedMonth"
          type="month"
          class="month-input"
          @change="handleMonthChange"
        >
      </div>
    </div>

    <div v-if="message" class="success-msg">{{ message }}</div>
    <div v-if="store.error || error" class="error-msg">{{ store.error || error }}</div>

    <section v-if="store.summary" class="budget-summary-grid">
      <div class="card summary-card">
        <span class="label">{{ t('budgets.totalBudget') }} ({{ t('common.all') }})</span>
        <strong class="value">{{ formatCurrency(store.summary.totalBudget) }}</strong>
      </div>
      <div class="card summary-card">
        <span class="label">{{ t('budgets.spentLabel') }}</span>
        <strong class="value">{{ formatCurrency(store.summary.totalUsed) }}</strong>
      </div>
      <div class="card summary-card">
        <span class="label">{{ t('budgets.remaining') }}</span>
        <strong class="value" :class="{ 'text-danger': store.summary.totalRemaining < 0 }">
          {{ formatCurrency(store.summary.totalRemaining) }}
        </strong>
      </div>
    </section>

    <section class="card form-card">
      <h2>{{ t('budgets.formTitle') }}</h2>
      <form class="form-row" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="budget-category">{{ t('budgets.category') }}</label>
          <select id="budget-category" v-model="form.category" required :disabled="editingId !== null">
            <option value="" disabled>{{ t('expenses.selectCategory') }}</option>
            <option v-for="category in categories" :key="category" :value="category">{{ translateCategory(t, category) }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="budget-limit">{{ t('budgets.monthlyLimit') }}</label>
          <input
            id="budget-limit"
            v-model.number="form.amount"
            type="number"
            step="1"
            min="0"
            placeholder="10000"
            required
          >
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="store.submitting">
            {{ store.submitting ? t('budgets.saveLoading') : t('budgets.saveAction') }}
          </button>
          <button v-if="editingId" type="button" class="btn btn-secondary" @click="cancelEdit">
            {{ t('common.cancel') }}
          </button>
        </div>
      </form>
    </section>

    <section class="card list-card">
      <h2>{{ t('budgets.currentStatus') }}</h2>

      <div v-if="store.loading || store.summaryLoading" class="loading-text">{{ t('budgets.loading') }}</div>
      <div v-else-if="!store.summary?.items?.length" class="empty-state">{{ t('common.empty') }}</div>

      <div v-else class="budget-list">
        <article v-for="item in store.summary.items" :key="item.category" class="budget-item" :class="`status-${item.status}`">
          <div class="budget-topline">
            <div class="info">
              <strong>{{ translateCategory(t, item.category) }}</strong>
              <div class="budget-meta">
                {{ t('budgets.limitLabel') }} {{ formatCurrency(item.budget) }} | {{ t('budgets.spentLabel') }} {{ formatCurrency(item.used) }}
              </div>
            </div>

            <div class="actions">
              <button class="btn btn-sm btn-secondary" @click="startEdit(item)">
                {{ t('common.edit') }}
              </button>
              <button class="btn btn-sm btn-danger" :disabled="store.deleting" @click="handleDelete(item.id)">
                {{ t('common.delete') }}
              </button>
            </div>
          </div>

          <div class="progress-track">
            <div
              class="progress-fill"
              :class="`progress-fill-${item.status}`"
              :style="{ width: `${Math.min(item.usageRate, 100)}%` }"
            />
          </div>

          <div class="budget-footer">
            <div class="usage-rate">
              <span class="status-icon" v-if="item.status === 'over'">!</span>
              <span class="status-icon" v-else-if="item.status === 'warning'">~</span>
              {{ item.usageRate }}% {{ t('budgets.used') }}
            </div>
            <div class="remaining" :class="{ 'text-danger': item.remaining < 0 }">
              <span v-if="item.remaining < 0">
                {{ t('budgets.overBy') }} {{ formatCurrency(Math.abs(item.remaining)) }}
              </span>
              <span v-else>
                {{ t('budgets.remaining') }} {{ formatCurrency(item.remaining) }}
              </span>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { EXPENSE_CATEGORIES } from '@/constants/categories'
import { useBudgetStore } from '@/stores/budgetStore'
import { translateCategory } from '@/utils/categories'
import { formatCurrency as formatCurrencyValue } from '@/utils/formatters'

const store = useBudgetStore()
const { t, locale } = useI18n()
const categories = EXPENSE_CATEGORIES

const message = ref('')
const error = ref('')
const editingId = ref(null)

const form = ref({
  category: '',
  amount: null
})

function formatCurrency(value) {
  return formatCurrencyValue(value, locale.value)
}

async function handleMonthChange() {
  await store.setSelectedMonth(store.selectedMonth)
}

function startEdit(item) {
  editingId.value = item.id
  form.value = {
    category: item.category,
    amount: item.budget
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editingId.value = null
  form.value = { category: '', amount: null }
}

async function handleSubmit() {
  message.value = ''
  error.value = ''
  try {
    if (editingId.value) {
      await store.modifyBudget(editingId.value, { amount: form.value.amount })
    } else {
      await store.saveBudget(form.value)
    }
    message.value = t('budgets.saved')
    cancelEdit()
  } catch (err) {
    error.value = err.message || t('common.unknownError')
  }
}

async function handleDelete(id) {
  if (!confirm(t('common.yes'))) return
  message.value = ''
  error.value = ''
  try {
    await store.removeBudget(id)
    message.value = t('budgets.deleted')
  } catch (err) {
    error.value = err.message || t('common.unknownError')
  }
}

onMounted(() => {
  store.setSelectedMonth(store.selectedMonth)
})
</script>

<style scoped>
.budgets-page {
  display: grid;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.budget-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.form-card,
.list-card {
  padding: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  align-items: end;
}

.form-group {
  display: grid;
  gap: 8px;
}

.budget-list {
  display: grid;
  gap: 16px;
}

.budget-item {
  padding: 16px;
  border-radius: 16px;
  border: 1px solid #e4ebf2;
  background: #f9fbfd;
}

.budget-topline,
.budget-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.budget-meta,
.usage-rate,
.remaining {
  font-size: 12px;
  color: #546575;
}

.progress-track {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: #e8eef4;
  overflow: hidden;
  margin: 12px 0;
}

.progress-fill {
  height: 100%;
}

.progress-fill-safe {
  background: #1f8f5f;
}

.progress-fill-warning {
  background: #d6a300;
}

.progress-fill-over {
  background: #d04d48;
}

@media (max-width: 960px) {
  .page-header,
  .budget-summary-grid,
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
