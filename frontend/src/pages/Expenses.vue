<template>
  <div>
    <div class="page-header">
      <h1>{{ t('expenses.title') }}</h1>
      <p>{{ t('expenses.subtitle') }}</p>
    </div>

    <section class="card">
      <h2>{{ t('expenses.addRecord') }}</h2>

      <div v-if="formError || store.error" class="error-msg">{{ formError || store.error }}</div>

      <form class="form-row" @submit.prevent="handleAdd">
        <div class="form-group">
          <label for="expense-amount">{{ t('common.amount') }}</label>
          <input id="expense-amount" v-model.number="form.amount" type="number" min="0.01" step="0.01" :placeholder="t('expenses.amountPlaceholder')" />
        </div>

        <div class="form-group">
          <label for="expense-type">{{ t('common.type') }}</label>
          <select id="expense-type" v-model="form.type">
            <option value="expense">{{ t('expenses.typeExpense') }}</option>
            <option value="income">{{ t('expenses.typeIncome') }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="expense-category">{{ t('common.category') }}</label>
          <select id="expense-category" v-model="form.category">
            <option value="" disabled>{{ t('expenses.selectCategory') }}</option>
            <option v-for="category in activeCategories" :key="category" :value="category">{{ translateCategory(t, category) }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="expense-date">{{ t('common.date') }}</label>
          <input id="expense-date" v-model="form.date" type="date" />
        </div>

        <div class="form-group note-group">
          <label for="expense-note">{{ t('common.note') }}</label>
          <input id="expense-note" v-model.trim="form.note" type="text" :placeholder="t('expenses.notePlaceholder')" />
        </div>

        <button class="btn btn-primary" :disabled="store.submitting">
          {{ store.submitting ? t('expenses.addLoading') : t('expenses.addAction') }}
        </button>
      </form>
    </section>

    <section class="card">
      <h2>{{ t('expenses.filters') }}</h2>

      <div class="form-row">
        <div class="form-group">
          <label for="filter-type">{{ t('common.type') }}</label>
          <select id="filter-type" v-model="filterType" @change="handleFilter">
            <option value="">{{ t('common.all') }}</option>
            <option value="income">{{ t('expenses.typeIncome') }}</option>
            <option value="expense">{{ t('expenses.typeExpense') }}</option>
          </select>
        </div>

        <button class="btn btn-secondary" @click="resetFilter">{{ t('common.resetFilter') }}</button>
      </div>
    </section>

    <section class="card">
      <h2>{{ t('expenses.records') }}</h2>

      <div v-if="store.loading" class="loading-text">{{ t('expenses.loading') }}</div>
      <div v-else-if="store.expenses.length === 0" class="empty-state">{{ t('common.empty') }}</div>

      <template v-else>
        <table class="table">
          <thead>
            <tr>
              <th>{{ t('common.date') }}</th>
              <th>{{ t('common.type') }}</th>
              <th>{{ t('common.category') }}</th>
              <th>{{ t('common.amount') }}</th>
              <th>{{ t('common.note') }}</th>
              <th>{{ t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in store.expenses" :key="item.id">
              <td>{{ item.date }}</td>
              <td>
                <span class="badge" :class="item.type === 'income' ? 'badge-success' : 'badge-danger'">
                  {{ item.type === 'income' ? t('expenses.typeIncome') : t('expenses.typeExpense') }}
                </span>
              </td>
              <td>{{ translateCategory(t, item.category) }}</td>
              <td :class="item.type === 'income' ? 'amount-income' : 'amount-expense'">
                {{ item.type === 'income' ? '+' : '-' }}{{ formatCurrency(item.amount) }}
              </td>
              <td>{{ item.note || '-' }}</td>
              <td>
                <button class="btn btn-danger" :disabled="store.deleting" @click="handleDelete(item.id)">
                  {{ store.deleting ? t('expenses.deleteLoading') : t('expenses.deleteAction') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="summary-row">
          <span>{{ t('expenses.totalIncome') }} <strong class="amount-income">{{ formatCurrency(store.totalIncome) }}</strong></span>
          <span>{{ t('expenses.totalExpense') }} <strong class="amount-expense">{{ formatCurrency(store.totalExpense) }}</strong></span>
          <span>
            {{ t('expenses.net') }}
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
import { useI18n } from 'vue-i18n'
import { EXPENSE_CATEGORIES, INCOME_CATEGORIES } from '@/constants/categories'
import { useExpenseStore } from '@/stores/expenseStore'
import { translateCategory } from '@/utils/categories'
import { getLocalDate } from '@/utils/date'
import { formatCurrency as formatCurrencyValue } from '@/utils/formatters'

const store = useExpenseStore()
const filterType = ref('')
const formError = ref('')
const today = getLocalDate()
const { t, locale } = useI18n()

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
  return formatCurrencyValue(value, locale.value)
}

async function handleAdd() {
  formError.value = ''

  if (!form.value.amount || form.value.amount <= 0) {
    formError.value = t('expenses.amountError')
    return
  }

  if (!form.value.category) {
    formError.value = t('expenses.categoryError')
    return
  }

  if (!form.value.date) {
    formError.value = t('expenses.dateError')
    return
  }

  try {
    filterType.value = ''
    await store.addExpense({ ...form.value }, { refreshParams: {} })
    form.value = {
      amount: null,
      type: 'expense',
      category: '',
      date: today,
      note: ''
    }
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
