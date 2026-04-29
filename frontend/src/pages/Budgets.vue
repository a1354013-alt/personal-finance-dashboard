<template>
  <div>
    <div class="page-header">
      <h1>{{ t('budgets.title') }}</h1>
      <p>{{ t('budgets.subtitle') }}</p>
    </div>

    <div v-if="message" class="success-msg">{{ message }}</div>
    <div v-if="store.error || error" class="error-msg">{{ store.error || error }}</div>

    <section class="card">
      <h2>{{ t('budgets.formTitle') }}</h2>
      <form class="form-row" @submit.prevent="handleAddBudget">
        <div class="form-group">
          <label for="budget-category">{{ t('budgets.category') }}</label>
          <select id="budget-category" v-model="newBudget.category" required>
            <option value="" disabled>{{ t('expenses.selectCategory') }}</option>
            <option v-for="category in categories" :key="category" :value="category">{{ translateCategory(t, category) }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="budget-limit">{{ t('budgets.monthlyLimit') }}</label>
          <input
            id="budget-limit"
            v-model.number="newBudget.monthly_limit"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="9000"
            required
          />
        </div>

        <button type="submit" class="btn btn-primary" :disabled="store.submitting">
          {{ store.submitting ? t('budgets.saveLoading') : t('budgets.saveAction') }}
        </button>
      </form>
    </section>

    <section class="card">
      <h2>{{ t('budgets.currentStatus') }}</h2>

      <div v-if="store.loading" class="loading-text">{{ t('budgets.loading') }}</div>
      <div v-else-if="store.budgets.length === 0" class="empty-state">{{ t('common.empty') }}</div>

      <div v-else class="budget-list">
        <article v-for="budget in store.budgets" :key="budget.id" class="budget-item">
          <div class="budget-topline">
            <div>
              <strong>{{ translateCategory(t, budget.category) }}</strong>
              <div class="budget-meta">
                {{ t('budgets.limitLabel') }} {{ formatCurrency(budget.monthly_limit) }} | {{ t('budgets.spentLabel') }} {{ formatCurrency(budget.current_spent) }}
              </div>
            </div>

            <button class="btn btn-danger" :disabled="store.deleting" @click="handleDeleteBudget(budget.id)">
              {{ store.deleting ? t('budgets.deleteLoading') : t('common.delete') }}
            </button>
          </div>

          <div class="progress-track">
            <div
              class="progress-fill"
              :class="progressClass(budget.percent_used)"
              :style="{ width: `${Math.min(budget.percent_used, 100)}%` }"
            />
          </div>

          <div class="budget-footer">
            <span>{{ formatPercent(budget.percent_used) }} {{ t('budgets.used') }}</span>
            <span v-if="budget.percent_used > 100" class="over-limit">
              {{ t('budgets.overBy') }} {{ formatCurrency(budget.current_spent - budget.monthly_limit) }}
            </span>
            <span v-else>{{ t('budgets.remaining') }} {{ formatCurrency(budget.monthly_limit - budget.current_spent) }}</span>
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
import { formatCurrency as formatCurrencyValue, formatPercent as formatPercentValue } from '@/utils/formatters'

const store = useBudgetStore()
const message = ref('')
const error = ref('')
const { t, locale } = useI18n()

const categories = EXPENSE_CATEGORIES

const newBudget = ref({
  category: '',
  monthly_limit: null
})

function formatCurrency(value) {
  return formatCurrencyValue(value, locale.value)
}

function formatPercent(value) {
  return formatPercentValue(value, locale.value)
}

function progressClass(percentUsed) {
  if (percentUsed > 100) return 'progress-fill-danger'
  if (percentUsed >= 80) return 'progress-fill-warning'
  return 'progress-fill-success'
}

async function fetchBudgets() {
  error.value = ''
  await store.fetchBudgets()
}

async function handleAddBudget() {
  message.value = ''
  error.value = ''

  try {
    await store.saveBudget(newBudget.value)
    message.value = t('budgets.saved')
    newBudget.value = { category: '', monthly_limit: null }
  } catch (err) {
    error.value = err.message || t('common.unknownError')
  }
}

async function handleDeleteBudget(id) {
  message.value = ''
  error.value = ''

  try {
    await store.removeBudget(id)
    message.value = t('budgets.deleted')
  } catch (err) {
    error.value = err.message || t('common.unknownError')
  }
}

onMounted(fetchBudgets)
</script>

<style scoped>
.budget-list {
  display: grid;
  gap: 16px;
}

.budget-item {
  padding: 16px;
  border: 1px solid #e4ebf2;
  border-radius: 12px;
  background: #f9fbfd;
}

.budget-topline {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
  align-items: center;
}

.budget-meta {
  margin-top: 4px;
  font-size: 13px;
  color: #66788a;
}

.progress-track {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: #e8eef4;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
}

.progress-fill-success {
  background: #1f8f5f;
}

.progress-fill-warning {
  background: #d6a300;
}

.progress-fill-danger {
  background: #d04d48;
}

.budget-footer {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 10px;
  font-size: 13px;
  color: #546575;
}

.over-limit {
  color: #9a2c2c;
  font-weight: 700;
}
</style>
