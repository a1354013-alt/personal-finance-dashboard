<template>
  <div class="budgets-page">
    <div class="page-header">
      <div class="header-content">
        <h1>{{ t('budgets.title') }}</h1>
        <p>{{ t('budgets.subtitle') }}</p>
      </div>
      <div class="month-selector">
        <input 
          type="month" 
          v-model="store.selectedMonth" 
          @change="handleMonthChange"
          class="month-input"
        />
      </div>
    </div>

    <div v-if="message" class="success-msg">{{ message }}</div>
    <div v-if="store.error || error" class="error-msg">{{ store.error || error }}</div>

    <!-- Summary Section -->
    <section v-if="store.summary" class="budget-summary-grid">
      <div class="card summary-card">
        <span class="label">{{ t('dashboard.summary.income') }} ({{ t('common.all') }})</span>
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

    <!-- Budget Form -->
    <section class="card form-card">
      <h2>{{ editingId ? t('budgets.formTitle') : t('budgets.formTitle') }}</h2>
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
          />
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

    <!-- Budget List -->
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
                {{ t('common.save') }}
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
              <span class="status-icon" v-if="item.status === 'over'">⚠️</span>
              <span class="status-icon" v-if="item.status === 'warning'">⚡</span>
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
      message.value = t('budgets.saved')
    } else {
      await store.saveBudget(form.value)
      message.value = t('budgets.saved')
    }
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

.month-input {
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid #d1d9e0;
  font-family: inherit;
  font-size: 15px;
  color: #233441;
}

.budget-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.summary-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
}

.summary-card .label {
  font-size: 13px;
  color: #627484;
  font-weight: 700;
}

.summary-card .value {
  font-size: 24px;
  font-weight: 800;
}

.form-card {
  padding: 24px;
}

.form-actions {
  display: flex;
  gap: 12px;
}

.list-card {
  padding: 24px;
}

.budget-list {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.budget-item {
  padding: 20px;
  border: 1px solid #e4ebf2;
  border-radius: 16px;
  background: #f9fbfd;
  transition: transform 0.2s ease;
}

.budget-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.04);
}

.budget-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.budget-topline .actions {
  display: flex;
  gap: 8px;
}

.btn-sm {
  min-height: 32px;
  padding: 4px 12px;
  font-size: 12px;
}

.budget-meta {
  margin-top: 4px;
  font-size: 13px;
  color: #66788a;
}

.progress-track {
  width: 100%;
  height: 12px;
  border-radius: 999px;
  background: #e8eef4;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.4s ease;
}

.progress-fill-safe { background: #1f8f5f; }
.progress-fill-warning { background: #d6a300; }
.progress-fill-over { background: #d04d48; }

.budget-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 14px;
  font-weight: 600;
}

.status-icon {
  margin-right: 4px;
}

.text-danger {
  color: #d04d48 !important;
}

@media (max-width: 640px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  .form-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
