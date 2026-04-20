<template>
  <div>
    <div class="page-header">
      <h1>Dashboard</h1>
      <p>Version {{ VERSION }}. Totals are all-time, while over-budget alerts are for the current month.</p>
    </div>

    <div v-if="store.loading" class="loading-text">Loading dashboard...</div>
    <div v-else-if="store.error" class="error-msg">{{ store.error }}</div>

    <template v-else-if="store.summary">
      <div class="stats-grid">
        <div class="card stat-card">
          <div class="card-label">All-time Income</div>
          <div class="stat-value income">{{ formatCurrency(store.summary.total_income) }}</div>
        </div>
        <div class="card stat-card">
          <div class="card-label">All-time Expense</div>
          <div class="stat-value expense">{{ formatCurrency(store.summary.total_expense) }}</div>
        </div>
        <div class="card stat-card">
          <div class="card-label">All-time Net Balance</div>
          <div class="stat-value balance" :class="store.summary.net_balance >= 0 ? 'income' : 'expense'">
            {{ formatCurrency(store.summary.net_balance) }}
          </div>
        </div>
      </div>

      <section class="card">
        <h2>Monthly Trend</h2>
        <div v-if="store.summary.monthly_trend.length === 0" class="empty-state">No trend data yet.</div>
        <div v-else class="trend-list">
          <div v-for="item in store.summary.monthly_trend" :key="item.month" class="trend-item">
            <div class="trend-month">{{ item.month }}</div>
            <div class="trend-metrics">
              <span class="income-text">Income {{ formatCurrency(item.income) }}</span>
              <span class="expense-text">Expense {{ formatCurrency(item.expense) }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="card">
        <h2>Expense by Category</h2>
        <div v-if="store.summary.expense_by_category.length === 0" class="empty-state">No expense data yet.</div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Amount</th>
              <th>Share</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in store.summary.expense_by_category" :key="item.category">
              <td>{{ item.category }}</td>
              <td>{{ formatCurrency(item.amount) }}</td>
              <td>{{ percent(item.amount, store.summary.total_expense).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="card">
        <h2>Over Budget (Current Month)</h2>
        <div v-if="store.summary.over_budget.length === 0" class="empty-state">No categories are over budget this month.</div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Limit</th>
              <th>Spent</th>
              <th>Over</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in store.summary.over_budget" :key="item.category">
              <td>{{ item.category }}</td>
              <td>{{ formatCurrency(item.limit) }}</td>
              <td>{{ formatCurrency(item.spent) }}</td>
              <td class="expense-text">{{ formatCurrency(item.over) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="card">
        <h2>AI Insights</h2>
        <div class="ai-block">
          <h3>Finance Summary</h3>
          <button v-if="!store.aiSummary" class="btn btn-primary" @click="store.fetchAiSummary()">Generate Summary</button>
          <p v-else class="ai-text">{{ store.aiSummary }}</p>
        </div>

        <div class="ai-block">
          <h3>Budget Advice</h3>
          <div v-if="store.budgetAdviceLoading" class="loading-text">Loading budget advice...</div>
          <div v-else-if="store.budgetAdviceError" class="error-msg">{{ store.budgetAdviceError }}</div>
          <button v-else-if="!store.budgetAdvice" class="btn btn-secondary" @click="store.fetchBudgetAdvice()">
            Get Advice
          </button>
          <p v-else class="ai-text ai-warning">{{ store.budgetAdvice }}</p>
        </div>
      </section>
    </template>

    <div v-else class="empty-state">No dashboard data available.</div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { VERSION } from '@/constants/version'
import { useDashboardStore } from '@/stores/dashboardStore'

const store = useDashboardStore()

function formatCurrency(value) {
  return `NT$ ${Number(value || 0).toLocaleString('zh-TW', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
}

function percent(value, total) {
  return total > 0 ? (value / total) * 100 : 0
}

onMounted(() => {
  store.fetchSummary()
  store.fetchBudgetAdvice()
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.stat-card {
  text-align: center;
}

.card-label {
  margin-bottom: 10px;
  color: #66788a;
  font-size: 13px;
}

.trend-list {
  display: grid;
  gap: 10px;
}

.trend-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #f8fbfe;
  border: 1px solid #e4ebf2;
}

.trend-month {
  font-weight: 700;
}

.trend-metrics {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.income-text {
  color: #1f8f5f;
}

.expense-text {
  color: #d04d48;
}

.ai-block + .ai-block {
  margin-top: 20px;
}

.ai-block h3 {
  margin-bottom: 10px;
  font-size: 15px;
}

.ai-text {
  margin: 0;
  padding: 12px 14px;
  background: #f5f8fc;
  border-radius: 10px;
  border-left: 4px solid #1d6fdc;
  line-height: 1.7;
  white-space: pre-line;
}

.ai-warning {
  border-left-color: #d6a300;
}
</style>
