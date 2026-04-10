<template>
  <div>
    <div class="page-header">
      <h1>Expenses</h1>
      <p>Track income and spending with a single consistent contract across the form, store, and API.</p>
    </div>

    <section class="card">
      <h2>Add Record</h2>

      <div v-if="formError || store.error" class="error-msg">{{ formError || store.error }}</div>

      <form class="form-row" @submit.prevent="handleAdd">
        <div class="form-group">
          <label for="expense-amount">Amount</label>
          <input id="expense-amount" v-model.number="form.amount" type="number" min="0.01" step="0.01" placeholder="1500" />
        </div>

        <div class="form-group">
          <label for="expense-type">Type</label>
          <select id="expense-type" v-model="form.type">
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
        </div>

        <div class="form-group">
          <label for="expense-category">Category</label>
          <select id="expense-category" v-model="form.category">
            <option value="" disabled>Select a category</option>
            <option v-for="category in activeCategories" :key="category" :value="category">{{ category }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="expense-date">Date</label>
          <input id="expense-date" v-model="form.date" type="date" />
        </div>

        <div class="form-group note-group">
          <label for="expense-note">Note</label>
          <input id="expense-note" v-model.trim="form.note" type="text" placeholder="Optional note" />
        </div>

        <button class="btn btn-primary" :disabled="store.submitting">
          {{ store.submitting ? 'Saving...' : 'Add Record' }}
        </button>
      </form>
    </section>

    <section class="card">
      <h2>Filters</h2>

      <div class="form-row">
        <div class="form-group">
          <label for="filter-type">Type</label>
          <select id="filter-type" v-model="filterType" @change="handleFilter">
            <option value="">All</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
        </div>

        <button class="btn btn-secondary" @click="resetFilter">Reset Filter</button>
      </div>
    </section>

    <section class="card">
      <h2>Records</h2>

      <div v-if="store.loading" class="loading-text">Loading records...</div>
      <div v-else-if="store.expenses.length === 0" class="empty-state">No records yet.</div>

      <template v-else>
        <table class="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Category</th>
              <th>Amount</th>
              <th>Note</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in store.expenses" :key="item.id">
              <td>{{ item.date }}</td>
              <td>
                <span class="badge" :class="item.type === 'income' ? 'badge-success' : 'badge-danger'">
                  {{ item.type }}
                </span>
              </td>
              <td>{{ item.category }}</td>
              <td :class="item.type === 'income' ? 'amount-income' : 'amount-expense'">
                {{ item.type === 'income' ? '+' : '-' }}{{ formatCurrency(item.amount) }}
              </td>
              <td>{{ item.note || '-' }}</td>
              <td>
                <button class="btn btn-danger" @click="handleDelete(item.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="summary-row">
          <span>Total Income <strong class="amount-income">{{ formatCurrency(store.totalIncome) }}</strong></span>
          <span>Total Expense <strong class="amount-expense">{{ formatCurrency(store.totalExpense) }}</strong></span>
          <span>
            Net
            <strong :class="store.totalIncome - store.totalExpense >= 0 ? 'amount-income' : 'amount-expense'">
              {{ formatCurrency(store.totalIncome - store.totalExpense) }}
            </strong>
          </span>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { EXPENSE_CATEGORIES, INCOME_CATEGORIES } from '@/constants/categories'
import { useExpenseStore } from '@/stores/expenseStore'

const store = useExpenseStore()
const filterType = ref('')
const formError = ref('')
const today = new Date().toISOString().split('T')[0]

const form = ref({
  amount: null,
  type: 'expense',
  category: '',
  date: today,
  note: ''
})

const activeCategories = computed(() => (form.value.type === 'income' ? INCOME_CATEGORIES : EXPENSE_CATEGORIES))

watch(
  () => form.value.type,
  () => {
    form.value.category = ''
  }
)

onMounted(() => {
  store.fetchExpenses()
})

function formatCurrency(value) {
  return `NT$ ${Number(value || 0).toLocaleString('zh-TW', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
}

async function handleAdd() {
  formError.value = ''

  if (!form.value.amount || form.value.amount <= 0) {
    formError.value = 'Amount must be greater than 0.'
    return
  }

  if (!form.value.category) {
    formError.value = 'Please select a category.'
    return
  }

  if (!form.value.date) {
    formError.value = 'Please select a date.'
    return
  }

  try {
    await store.addExpense({ ...form.value })
    form.value = {
      amount: null,
      type: 'expense',
      category: '',
      date: today,
      note: ''
    }
    filterType.value = ''
  } catch (_error) {
    // Store error is already shown above.
  }
}

async function handleDelete(id) {
  try {
    await store.removeExpense(id)
  } catch (_error) {
    // Store error is already shown above.
  }
}

function handleFilter() {
  store.fetchExpenses(filterType.value ? { type: filterType.value } : {})
}

function resetFilter() {
  filterType.value = ''
  store.fetchExpenses()
}
</script>

<style scoped>
.note-group {
  min-width: 240px;
}

.summary-row {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e7edf3;
  color: #546575;
}

.amount-income {
  color: #1f8f5f;
  font-weight: 700;
}

.amount-expense {
  color: #d04d48;
  font-weight: 700;
}
</style>
