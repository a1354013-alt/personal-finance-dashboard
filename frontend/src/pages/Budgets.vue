<template>
  <div>
    <div class="page-header">
      <h1>Budgets</h1>
      <p>Monthly budget status is calculated from current-month expense records only.</p>
    </div>

    <div v-if="message" class="success-msg">{{ message }}</div>
    <div v-if="store.error || error" class="error-msg">{{ store.error || error }}</div>

    <section class="card">
      <h2>Create or Update Budget</h2>
      <form class="form-row" @submit.prevent="handleAddBudget">
        <div class="form-group">
          <label for="budget-category">Category</label>
          <select id="budget-category" v-model="newBudget.category" required>
            <option value="" disabled>Select a category</option>
            <option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="budget-limit">Monthly Limit</label>
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
          {{ store.submitting ? 'Saving...' : 'Save Budget' }}
        </button>
      </form>
    </section>

    <section class="card">
      <h2>Current Month Status</h2>

      <div v-if="store.loading" class="loading-text">Loading budgets...</div>
      <div v-else-if="store.budgets.length === 0" class="empty-state">No budgets yet.</div>

      <div v-else class="budget-list">
        <article v-for="budget in store.budgets" :key="budget.id" class="budget-item">
          <div class="budget-topline">
            <div>
              <strong>{{ budget.category }}</strong>
              <div class="budget-meta">
                Limit {{ formatCurrency(budget.monthly_limit) }} · Spent {{ formatCurrency(budget.current_spent) }}
              </div>
            </div>

            <button class="btn btn-danger" @click="handleDeleteBudget(budget.id)">Delete</button>
          </div>

          <div class="progress-track">
            <div
              class="progress-fill"
              :class="progressClass(budget.percent_used)"
              :style="{ width: `${Math.min(budget.percent_used, 100)}%` }"
            />
          </div>

          <div class="budget-footer">
            <span>{{ budget.percent_used.toFixed(1) }}% used</span>
            <span v-if="budget.percent_used > 100" class="over-limit">
              Over by {{ formatCurrency(budget.current_spent - budget.monthly_limit) }}
            </span>
            <span v-else>Remaining {{ formatCurrency(budget.monthly_limit - budget.current_spent) }}</span>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { EXPENSE_CATEGORIES } from '@/constants/categories'
import { useBudgetStore } from '@/stores/budgetStore'

const store = useBudgetStore()
const message = ref('')
const error = ref('')

const categories = EXPENSE_CATEGORIES

const newBudget = ref({
  category: '',
  monthly_limit: null
})

function formatCurrency(value) {
  return `NT$ ${Number(value || 0).toLocaleString('zh-TW', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
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
    message.value = 'Budget saved successfully.'
    newBudget.value = { category: '', monthly_limit: null }
  } catch (err) {
    error.value = err.message || 'Unable to save budget.'
  }
}

async function handleDeleteBudget(id) {
  message.value = ''
  error.value = ''

  try {
    await store.removeBudget(id)
    message.value = 'Budget deleted.'
  } catch (err) {
    error.value = err.message || 'Unable to delete budget.'
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
