<template>
  <div class="dashboard-page">
    <div class="page-header hero-header">
      <div>
        <p class="eyebrow">Control Center</p>
        <h1>Financial clarity that feels alive</h1>
        <p>Version {{ VERSION }}. Trends, budget health, and AI context update from the same normalized API layer.</p>
      </div>
    </div>

    <OnboardingCard
      v-if="isFirstTimeUser"
      title="Start with three small moves"
      description="The dashboard becomes far more useful once it has a few expenses, one budget, and at least one stock to monitor."
      :steps="[
        'Add your first expense or income record.',
        'Create a budget for one category you care about most.',
        'Open Stocks and add a watchlist symbol to populate market context.'
      ]"
    />

    <div v-if="store.loading" class="stats-grid">
      <SkeletonCard v-for="index in 3" :key="index" />
    </div>
    <div v-else-if="store.error" class="error-msg">{{ store.error }}</div>

    <template v-else-if="store.summary">
      <div class="stats-grid">
        <section class="card stat-card income-card">
          <div class="card-label">All-time Income</div>
          <div class="stat-value income">{{ formatCurrency(store.summary.total_income) }}</div>
          <div class="card-note">Captured across every recorded period.</div>
        </section>
        <section class="card stat-card expense-card">
          <div class="card-label">All-time Expense</div>
          <div class="stat-value expense">{{ formatCurrency(store.summary.total_expense) }}</div>
          <div class="card-note">Used for trend and category distribution.</div>
        </section>
        <section class="card stat-card balance-card">
          <div class="card-label">All-time Net Balance</div>
          <div class="stat-value" :class="store.summary.net_balance >= 0 ? 'income' : 'expense'">
            {{ formatCurrency(store.summary.net_balance) }}
          </div>
          <div class="card-note">A quick sense of long-term financial momentum.</div>
        </section>
      </div>

      <div class="charts-grid">
        <ChartPanel
          title="Monthly Expense Trend"
          subtitle="Expense totals by month"
          :loading="store.chartsLoading"
          :error="store.chartsError || ''"
          :labels="expenseTrend.labels"
          :datasets="expenseTrend.datasets"
        />
        <ChartPanel
          title="Category Distribution"
          subtitle="Where spending is concentrated"
          type="pie"
          :loading="store.chartsLoading"
          :error="store.chartsError || ''"
          :labels="categoryDistribution.labels"
          :datasets="categoryDistribution.datasets"
        />
        <ChartPanel
          title="Net Income Trend"
          subtitle="Income vs expense over time"
          :loading="store.chartsLoading"
          :error="store.chartsError || ''"
          :labels="netIncomeTrend.labels"
          :datasets="netIncomeTrend.datasets"
        />

        <section class="card budget-usage-card">
          <h2>Budget Usage</h2>
          <div v-if="store.chartsLoading" class="budget-skeleton-list">
            <div v-for="index in 4" :key="index" class="budget-skeleton-row" />
          </div>
          <div v-else-if="store.chartsError" class="error-msg">{{ store.chartsError }}</div>
          <div v-else-if="!budgetUsage.length" class="empty-state">No data yet</div>
          <div v-else class="budget-usage-list">
            <article v-for="item in budgetUsage" :key="item.category" class="budget-usage-item">
              <div class="budget-usage-head">
                <strong>{{ item.category }}</strong>
                <span>{{ item.percent_used.toFixed(1) }}%</span>
              </div>
              <div class="progress-track">
                <div
                  class="progress-fill"
                  :class="progressClass(item.percent_used)"
                  :style="{ width: `${Math.min(item.percent_used, 100)}%` }"
                />
              </div>
              <div class="budget-usage-meta">
                <span>{{ formatCurrency(item.current_spent) }} spent</span>
                <span>{{ formatCurrency(item.monthly_limit) }} limit</span>
              </div>
            </article>
          </div>
        </section>
      </div>

      <div class="insights-grid">
        <section class="card">
          <div class="section-heading">
            <h2>AI Summary</h2>
            <button v-if="!store.aiSummaryLoading" class="btn btn-primary" @click="store.fetchAiSummary()">Refresh</button>
          </div>
          <div v-if="store.aiSummaryLoading" class="loading-text">Generating summary...</div>
          <div v-else-if="store.aiSummaryError" class="error-msg">{{ store.aiSummaryError }}</div>
          <p v-else-if="store.aiSummary" class="ai-text">{{ store.aiSummary }}</p>
          <div v-else class="empty-state">No data yet</div>
        </section>

        <section class="card">
          <div class="section-heading">
            <h2>Budget Advice</h2>
            <button v-if="!store.budgetAdviceLoading" class="btn btn-secondary" @click="store.fetchBudgetAdvice()">Refresh</button>
          </div>
          <div v-if="store.budgetAdviceLoading" class="loading-text">Loading budget advice...</div>
          <div v-else-if="store.budgetAdviceError" class="error-msg">{{ store.budgetAdviceError }}</div>
          <p v-else-if="store.budgetAdvice" class="ai-text ai-warning">{{ store.budgetAdvice }}</p>
          <div v-else class="empty-state">No data yet</div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import ChartPanel from '@/components/ChartPanel.vue'
import OnboardingCard from '@/components/OnboardingCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import { VERSION } from '@/constants/version'
import { useDashboardStore } from '@/stores/dashboardStore'

const store = useDashboardStore()

function formatCurrency(value) {
  return `NT$ ${Number(value || 0).toLocaleString('zh-TW', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
}

const isFirstTimeUser = computed(() => {
  const summary = store.summary
  if (!summary) return false
  return summary.total_income === 0 && summary.total_expense === 0 && !summary.expense_by_category.length
})

const expenseTrend = computed(() => ({
  labels: store.charts?.monthly_expense_trend?.map((item) => item.month) || [],
  datasets: [
    {
      label: 'Expense',
      data: store.charts?.monthly_expense_trend?.map((item) => item.expense) || [],
      borderColor: '#cf5c36',
      backgroundColor: 'rgba(207, 92, 54, 0.18)',
      fill: true,
      tension: 0.36
    }
  ]
}))

const categoryDistribution = computed(() => ({
  labels: store.charts?.category_distribution?.map((item) => item.category) || [],
  datasets: [
    {
      data: store.charts?.category_distribution?.map((item) => item.amount) || [],
      backgroundColor: ['#102b44', '#cf5c36', '#e4a45d', '#2f7a76', '#c7d3e2', '#6b7f95']
    }
  ]
}))

const netIncomeTrend = computed(() => ({
  labels: store.charts?.net_income_trend?.map((item) => item.month) || [],
  datasets: [
    {
      label: 'Income',
      data: store.charts?.net_income_trend?.map((item) => item.income) || [],
      borderColor: '#1d845a',
      backgroundColor: 'rgba(29, 132, 90, 0.14)',
      tension: 0.32
    },
    {
      label: 'Expense',
      data: store.charts?.net_income_trend?.map((item) => item.expense) || [],
      borderColor: '#102b44',
      backgroundColor: 'rgba(16, 43, 68, 0.08)',
      tension: 0.32
    }
  ]
}))

const budgetUsage = computed(() => store.charts?.budget_usage || [])

function progressClass(percentUsed) {
  if (percentUsed > 100) return 'progress-fill-danger'
  if (percentUsed >= 80) return 'progress-fill-warning'
  return 'progress-fill-success'
}

onMounted(() => {
  store.fetchSummary()
  store.fetchCharts()
  store.fetchAiSummary()
  store.fetchBudgetAdvice()
})
</script>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 20px;
}

.hero-header {
  padding: 24px 28px;
  border-radius: 20px;
  background:
    radial-gradient(circle at 20% 10%, rgba(228, 164, 93, 0.22), transparent 30%),
    linear-gradient(135deg, #102b44 0%, #214869 55%, #2f7a76 100%);
  color: #f7fbff;
}

.eyebrow {
  margin: 0 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 12px;
  color: rgba(255, 232, 204, 0.92);
}

.hero-header p:last-child {
  max-width: 720px;
  color: rgba(236, 244, 251, 0.95);
}

.stats-grid,
.charts-grid,
.insights-grid {
  display: grid;
  gap: 16px;
}

.stats-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.charts-grid {
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.insights-grid {
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.stat-card {
  overflow: hidden;
  position: relative;
}

.income-card::after,
.expense-card::after,
.balance-card::after {
  content: '';
  position: absolute;
  inset: auto -35px -35px auto;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  opacity: 0.18;
}

.income-card::after { background: #6ecf9f; }
.expense-card::after { background: #e7a885; }
.balance-card::after { background: #83cfd0; }

.card-label,
.card-note,
.budget-usage-meta {
  color: #66788a;
}

.card-note {
  margin-top: 10px;
  font-size: 13px;
}

.budget-usage-card {
  min-height: 340px;
}

.budget-usage-list {
  display: grid;
  gap: 14px;
}

.budget-usage-item {
  display: grid;
  gap: 8px;
}

.budget-usage-head,
.budget-usage-meta,
.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.progress-track {
  width: 100%;
  height: 12px;
  background: #e8eef4;
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
}

.progress-fill-success { background: #1d845a; }
.progress-fill-warning { background: #d58a1f; }
.progress-fill-danger { background: #cf5c36; }

.budget-skeleton-list {
  display: grid;
  gap: 16px;
}

.budget-skeleton-row {
  height: 54px;
  border-radius: 14px;
  background: linear-gradient(90deg, rgba(219, 228, 238, 0.7), rgba(244, 247, 250, 0.95), rgba(219, 228, 238, 0.7));
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.ai-text {
  margin: 0;
  padding: 14px 16px;
  border-radius: 14px;
  background: #f5f8fc;
  border-left: 4px solid #102b44;
  line-height: 1.7;
  white-space: pre-line;
}

.ai-warning {
  border-left-color: #cf5c36;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
