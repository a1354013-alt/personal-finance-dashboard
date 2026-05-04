<template>
  <div class="dashboard-page">
    <!-- Hero Section -->
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="hero-tag">{{ t('dashboard.heroTag') }}</p>
        <h1>{{ t('dashboard.heroTitle') }}</h1>
        <p class="hero-subtitle">{{ t('dashboard.heroSubtitle') }}</p>
        <div class="hero-meta">
          <span>{{ t('dashboard.heroVersion', { version: VERSION }) }}</span>
          <span>{{ todayLabel }}</span>
        </div>
      </div>

      <div class="hero-status-grid">
        <article class="hero-status-card">
          <span class="status-label">{{ t('dashboard.statusBalance') }}</span>
          <strong :class="{ 'text-danger': (store.summary?.monthlyBalance || 0) < 0 }">
            {{ formatCurrency(store.summary?.monthlyBalance || 0) }}
          </strong>
          <p>{{ (store.summary?.monthlyBalance || 0) >= 0 ? t('dashboard.summary.balanceNote') : t('dashboard.statusBudgetTight') }}</p>
        </article>
        <article class="hero-status-card">
          <span class="status-label">{{ t('dashboard.statusBudget') }}</span>
          <strong>{{ budgetHealthLabel }}</strong>
          <p>{{ budgetHealthDescription }}</p>
        </article>
        <article class="hero-status-card">
          <span class="status-label">{{ t('dashboard.statusAi') }}</span>
          <strong>{{ aiStatusLabel }}</strong>
          <p>{{ aiStatusDescription }}</p>
        </article>
      </div>
    </section>

    <!-- Onboarding for new users -->
    <OnboardingCard
      v-if="isFirstTimeUser"
      :title="t('dashboard.onboarding.title')"
      :description="t('dashboard.onboarding.description')"
      :steps="[
        t('dashboard.onboarding.stepOne'),
        t('dashboard.onboarding.stepTwo'),
        t('dashboard.onboarding.stepThree')
      ]"
    />

    <!-- Summary Cards -->
    <div v-if="store.loading && !store.summary" class="stats-grid">
      <SkeletonCard v-for="index in 4" :key="index" />
    </div>
    <div v-else class="stats-grid">
      <section
        v-for="item in statCards"
        :key="item.key"
        class="card summary-card"
        :class="`summary-card-${item.tone}`"
      >
        <div class="summary-card-head">
          <span class="summary-icon">{{ item.icon }}</span>
        </div>
        <div class="card-label">{{ item.title }}</div>
        <div class="stat-value" :class="item.valueClass">{{ item.value }}</div>
        <div class="card-note">{{ item.note }}</div>
      </section>
    </div>

    <div v-if="store.error && !store.summary" class="error-msg">{{ store.error }}</div>

    <!-- Charts Section -->
    <section class="insight-section">
      <div class="section-copy">
        <h2>{{ t('nav.dashboard') }}</h2>
        <p>{{ t('dashboard.insight.netIncomeTrendSubtitle') }}</p>
      </div>

      <div class="insight-grid">
        <!-- Monthly Trend Chart -->
        <ChartPanel
          :title="t('dashboard.insight.expenseTrend')"
          :subtitle="t('dashboard.insight.expenseTrendSubtitle')"
          :loading="store.loading"
          :error="store.error || ''"
          :labels="monthlyTrend.labels"
          :datasets="monthlyTrend.datasets"
        />
        
        <!-- Category Distribution Chart -->
        <ChartPanel
          :title="t('dashboard.insight.categoryDistribution')"
          :subtitle="t('dashboard.insight.categoryDistributionSubtitle')"
          type="pie"
          :loading="store.loading"
          :error="store.error || ''"
          :labels="categoryDistribution.labels"
          :datasets="categoryDistribution.datasets"
        />

        <!-- Recent Transactions Chart -->
        <ChartPanel
          :title="t('dashboard.recentTransactions.title')"
          :subtitle="t('dashboard.recentTransactions.subtitle')"
          type="bar"
          :loading="store.loading"
          :error="store.error || ''"
          :labels="recentTransactionsChart.labels"
          :datasets="recentTransactionsChart.datasets"
        />
      </div>
    </section>

    <!-- Recent Transactions List & Budget Health -->
    <div class="bottom-grid">
      <!-- Recent Transactions List -->
      <section class="card recent-list-card">
        <div class="section-heading">
          <div>
            <h2>{{ t('dashboard.recentTransactions.title') }}</h2>
            <p>{{ t('dashboard.recentTransactions.subtitle') }}</p>
          </div>
          <router-link to="/expenses" class="btn btn-secondary btn-sm">
            {{ t('common.all') }}
          </router-link>
        </div>

        <div v-if="store.loading && !store.summary" class="loading-placeholder">
          <div v-for="i in 5" :key="i" class="skeleton-row"></div>
        </div>
        <div v-else-if="!store.summary?.recentTransactions?.length" class="empty-state">
          <p>{{ t('dashboard.recentTransactions.noTransactions') }}</p>
        </div>
        <div v-else class="transaction-list">
          <div v-for="(tx, idx) in store.summary.recentTransactions" :key="idx" class="transaction-item">
            <div class="tx-info">
              <span class="tx-date">{{ tx.date }}</span>
              <span class="tx-category">{{ translateCategory(t, tx.category) }}</span>
            </div>
            <div class="tx-amount" :class="tx.type">
              {{ tx.type === 'income' ? '+' : '-' }} {{ formatCurrency(tx.amount) }}
            </div>
          </div>
        </div>
      </section>

      <!-- Budget Health -->
      <section class="budget-health-shell card">
        <div class="section-heading">
          <div>
            <h2>{{ t('dashboard.budgetHealth.title') }}</h2>
            <p>{{ t('dashboard.budgetHealth.subtitle') }}</p>
          </div>
          <router-link to="/budgets" class="btn btn-secondary btn-sm">
            {{ t('common.save') }}
          </router-link>
        </div>

        <div v-if="store.loading && !store.summary" class="budget-skeleton-list">
          <div v-for="index in 4" :key="index" class="budget-skeleton-row" />
        </div>
        <div v-else-if="!store.summary?.budgetItems?.length" class="empty-budget-state">
          <div class="budget-empty-visual" />
          <strong>{{ t('dashboard.empty.budgetTitle') }}</strong>
          <p>{{ t('dashboard.empty.budgetDescription') }}</p>
        </div>
        <div v-else class="budget-health-list">
          <article
            v-for="item in budgetUsage"
            :key="item.category"
            class="budget-health-item"
            :class="`budget-health-${item.status}`"
          >
            <div class="budget-topline">
              <div>
                <strong>{{ translateCategory(t, item.category) }}</strong>
                <div class="budget-inline-meta">
                  <span>{{ t('dashboard.budgetHealth.spent') }} {{ formatCurrency(item.used) }}</span>
                  <span>{{ t('dashboard.budgetHealth.limit') }} {{ formatCurrency(item.budget) }}</span>
                </div>
              </div>
              <div class="budget-status-meta">
                <span class="budget-status-pill">{{ t(`budgets.status.${item.status}`) }}</span>
                <strong>{{ item.usageRate }}%</strong>
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
              <span v-if="item.status === 'over'">
                {{ t('dashboard.budgetHealth.overBy') }} {{ formatCurrency(Math.abs(item.remaining)) }}
              </span>
              <span v-else>
                {{ t('dashboard.budgetHealth.remaining') }} {{ formatCurrency(item.remaining) }}
              </span>
            </div>
          </article>
        </div>
      </section>
    </div>

    <!-- AI Insights -->
    <section class="ai-grid">
      <article class="card ai-card">
        <div class="section-heading">
          <div>
            <h2>{{ t('dashboard.ai.summaryTitle') }}</h2>
            <p>{{ t('dashboard.ai.fallbackDescription') }}</p>
          </div>
          <button v-if="!store.aiSummaryLoading" class="btn btn-primary" @click="store.fetchAiSummary()">
            {{ t('dashboard.ai.refresh') }}
          </button>
        </div>

        <div v-if="store.aiSummaryLoading" class="loading-text">{{ t('dashboard.ai.loadingSummary') }}</div>
        <div v-else-if="displayAiSummary.isFallback" class="ai-fallback-shell">
          <div class="ai-fallback-banner">{{ t('dashboard.ai.fallbackSummary') }}</div>
          <p class="ai-text">{{ displayAiSummary.text }}</p>
        </div>
        <p v-else-if="displayAiSummary.text" class="ai-text">{{ displayAiSummary.text }}</p>
        <div v-else class="empty-budget-state compact">
          <div class="budget-empty-visual" />
          <strong>{{ t('dashboard.empty.aiTitle') }}</strong>
          <p>{{ t('dashboard.empty.aiDescription') }}</p>
        </div>
      </article>

      <article class="card ai-card">
        <div class="section-heading">
          <div>
            <h2>{{ t('dashboard.ai.adviceTitle') }}</h2>
            <p>{{ t('dashboard.ai.fallbackDescription') }}</p>
          </div>
          <button v-if="!store.budgetAdviceLoading" class="btn btn-secondary" @click="store.fetchBudgetAdvice()">
            {{ t('dashboard.ai.refresh') }}
          </button>
        </div>

        <div v-if="store.budgetAdviceLoading" class="loading-text">{{ t('dashboard.ai.loadingAdvice') }}</div>
        <div v-else-if="displayBudgetAdvice.isFallback" class="ai-fallback-shell">
          <div class="ai-fallback-banner">{{ t('dashboard.ai.fallbackSummary') }}</div>
          <p class="ai-text ai-warning">{{ displayBudgetAdvice.text }}</p>
        </div>
        <p v-else-if="displayBudgetAdvice.text" class="ai-text ai-warning">{{ displayBudgetAdvice.text }}</p>
        <div v-else class="empty-budget-state compact">
          <div class="budget-empty-visual" />
          <strong>{{ t('dashboard.empty.aiTitle') }}</strong>
          <p>{{ t('dashboard.empty.aiDescription') }}</p>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import ChartPanel from '@/components/ChartPanel.vue'
import OnboardingCard from '@/components/OnboardingCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import { VERSION } from '@/constants/version'
import { useDashboardStore } from '@/stores/dashboardStore'
import { translateCategory } from '@/utils/categories'
import { formatCurrency as formatCurrencyValue, formatPercent as formatPercentValue } from '@/utils/formatters'

const store = useDashboardStore()
const { t, locale } = useI18n()

const todayLabel = computed(() =>
  new Intl.DateTimeFormat(locale.value, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(new Date())
)

function formatCurrency(value) {
  return formatCurrencyValue(value, locale.value)
}

function formatPercent(value) {
  return formatPercentValue(value, locale.value)
}

const isFirstTimeUser = computed(() => {
  const summary = store.summary
  if (!summary) return false
  return summary.monthlyIncome === 0 && summary.monthlyExpense === 0 && !summary.expenseByCategory.length
})

// Charts Computeds
const monthlyTrend = computed(() => ({
  labels: store.summary?.monthlyTrend?.map((item) => item.month) || [],
  datasets: [
    {
      label: t('dashboard.summary.income'),
      data: store.summary?.monthlyTrend?.map((item) => item.income) || [],
      borderColor: '#2f7a76',
      backgroundColor: 'rgba(130, 201, 188, 0.24)',
      tension: 0.32
    },
    {
      label: t('dashboard.summary.expense'),
      data: store.summary?.monthlyTrend?.map((item) => item.expense) || [],
      borderColor: '#25465b',
      backgroundColor: 'rgba(157, 180, 197, 0.16)',
      tension: 0.32
    }
  ]
}))

const categoryDistribution = computed(() => ({
  labels: store.summary?.expenseByCategory?.map((item) => translateCategory(t, item.category)) || [],
  datasets: [
    {
      data: store.summary?.expenseByCategory?.map((item) => item.amount) || [],
      backgroundColor: ['#27556f', '#dd9f73', '#75a68f', '#8aa6c1', '#d4c1a5', '#b9d4cf']
    }
  ]
}))

const recentTransactionsChart = computed(() => ({
  labels: store.summary?.recentTransactions?.map((item, idx) => `${item.date} #${idx + 1}`) || [],
  datasets: [
    {
      label: t('common.amount'),
      data: store.summary?.recentTransactions?.map((item) => item.amount) || [],
      backgroundColor: store.summary?.recentTransactions?.map((item) => 
        item.type === 'income' ? 'rgba(130, 201, 188, 0.6)' : 'rgba(221, 159, 115, 0.6)'
      )
    }
  ]
}))

const budgetUsage = computed(() =>
  [...(store.summary?.budgetItems || [])].sort((a, b) => b.usageRate - a.usageRate)
)

const budgetHealthLabel = computed(() => {
  const over = store.summary?.budgetOverCount || 0
  const warning = store.summary?.budgetWarningCount || 0
  if (over > 0) return t('budgets.status.over')
  if (warning > 0) return t('budgets.status.warning')
  return t('budgets.status.safe')
})

const budgetHealthDescription = computed(() => {
  const over = store.summary?.budgetOverCount || 0
  const warning = store.summary?.budgetWarningCount || 0
  if (over > 0) return `${over} ${t('dashboard.budgetHealth.overTitle')}`
  if (warning > 0) return `${warning} ${t('dashboard.budgetHealth.warningTitle')}`
  return t('dashboard.statusAiReady')
})

const aiStatusLabel = computed(() => (
  store.aiSummaryError || store.budgetAdviceError ? t('dashboard.statusAiFallback') : t('dashboard.statusAiReady')
))

const aiStatusDescription = computed(() => {
  if (store.aiSummaryError || store.budgetAdviceError) {
    return t('dashboard.ai.fallbackDescription')
  }
  return budgetUsage.value.length ? `${t('dashboard.budgetHealth.title')} ${formatPercent(store.summary?.totalUsed / store.summary?.totalBudget * 100 || 0)}` : t('dashboard.statusAiReady')
})

const statCards = computed(() => [
  {
    key: 'income',
    icon: '💰',
    tone: 'income',
    title: t('dashboard.summary.monthlyIncome'),
    value: formatCurrency(store.summary?.monthlyIncome || 0),
    note: t('dashboard.summary.incomeNote'),
    valueClass: 'income'
  },
  {
    key: 'expense',
    icon: '💸',
    tone: 'expense',
    title: t('dashboard.summary.monthlyExpense'),
    value: formatCurrency(store.summary?.monthlyExpense || 0),
    note: t('dashboard.summary.expenseNote'),
    valueClass: 'expense'
  },
  {
    key: 'balance',
    icon: '⚖️',
    tone: 'balance',
    title: t('dashboard.summary.monthlyBalance'),
    value: formatCurrency(store.summary?.monthlyBalance || 0),
    note: t('dashboard.summary.balanceNote'),
    valueClass: (store.summary?.monthlyBalance || 0) >= 0 ? 'income' : 'expense'
  },
  {
    key: 'budget-remaining',
    icon: '🎯',
    tone: 'budget',
    title: t('budgets.remaining'),
    value: formatCurrency(store.summary?.totalRemaining || 0),
    note: `${t('budgets.limitLabel')} ${formatCurrency(store.summary?.totalBudget || 0)}`,
    valueClass: (store.summary?.totalRemaining || 0) >= 0 ? 'balance' : 'expense'
  }
])

const displayAiSummary = computed(() => {
  if (store.aiSummary && !store.aiSummaryError) {
    return { text: store.aiSummary, isFallback: false }
  }

  const highestExpense = categoryDistribution.value.labels[0]
  const fallbackText = highestExpense
    ? `${t('dashboard.ai.fallbackDescription')} ${t('dashboard.insight.categoryDistribution')}: ${highestExpense}`
    : t('dashboard.ai.fallbackSummary')

  return { text: fallbackText, isFallback: Boolean(store.aiSummaryError || !store.aiSummary) }
})

const displayBudgetAdvice = computed(() => {
  if (store.budgetAdvice && !store.budgetAdviceError) {
    return { text: store.budgetAdvice, isFallback: false }
  }

  const topBudget = budgetUsage.value[0]
  if (topBudget) {
    const statusText = t(`budgets.status.${topBudget.status}`)
    return {
      text: `${t('dashboard.ai.fallbackAdviceDefault')} ${translateCategory(t, topBudget.category)} ${statusText}，${topBudget.usageRate}%。`,
      isFallback: true
    }
  }

  return {
    text: t('dashboard.ai.fallbackAdviceDefault'),
    isFallback: Boolean(store.budgetAdviceError || !store.budgetAdvice)
  }
})

onMounted(() => {
  store.fetchSummary()
  store.fetchAiSummary()
  store.fetchBudgetAdvice()
})
</script>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 24px;
}

.hero-panel {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.9fr);
  gap: 22px;
  padding: 28px;
  border-radius: 32px;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(247, 227, 196, 0.92), transparent 34%),
    radial-gradient(circle at bottom right, rgba(183, 221, 205, 0.72), transparent 32%),
    linear-gradient(135deg, rgba(255, 252, 247, 0.92), rgba(238, 245, 247, 0.92));
  border: 1px solid rgba(220, 230, 236, 0.86);
  box-shadow: 0 26px 60px rgba(67, 88, 99, 0.08);
}

.hero-panel::after {
  content: '';
  position: absolute;
  inset: auto -80px -90px auto;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: rgba(130, 189, 173, 0.16);
}

.hero-copy {
  position: relative;
  z-index: 1;
}

.hero-tag {
  margin: 0 0 14px;
  color: #6f8a7c;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.24em;
}

.hero-copy h1 {
  margin: 0;
  max-width: 560px;
  font-size: clamp(34px, 5vw, 52px);
  line-height: 1.05;
  color: #213846;
}

.hero-subtitle {
  margin: 14px 0 0;
  max-width: 620px;
  font-size: 16px;
  line-height: 1.85;
  color: #5c6f7d;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.hero-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(211, 223, 229, 0.78);
  color: #536778;
  font-size: 13px;
}

.hero-status-grid {
  display: grid;
  gap: 14px;
  position: relative;
  z-index: 1;
}

.hero-status-card {
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(224, 232, 236, 0.82);
  box-shadow: 0 12px 30px rgba(79, 98, 109, 0.08);
  backdrop-filter: blur(8px);
}

.hero-status-card strong {
  display: block;
  margin-top: 6px;
  font-size: 24px;
  color: #1e3746;
}

.hero-status-card p {
  margin: 8px 0 0;
  color: #6a7b88;
  line-height: 1.7;
}

.status-label {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #6e8374;
  text-transform: uppercase;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.summary-card {
  position: relative;
  overflow: hidden;
  min-height: 160px;
  padding: 24px;
}

.summary-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 24px;
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.card-label {
  margin-top: 16px;
  font-size: 14px;
  color: #627585;
  font-weight: 600;
}

.stat-value {
  margin-top: 8px;
  font-size: 22px;
  font-weight: 800;
  color: #1e3746;
}

.card-note {
  margin-top: 8px;
  font-size: 12px;
  color: #8fa1b0;
}

.text-danger {
  color: #d9534f !important;
}

.income {
  color: #1f8f5f;
}

.expense {
  color: #d04d48;
}

.balance {
  color: #2b6cb0;
}

.summary-card-income {
  background: linear-gradient(135deg, #f0f9f6 0%, #e1f2ed 100%);
}

.summary-card-expense {
  background: linear-gradient(135deg, #fff5f0 0%, #ffede1 100%);
}

.summary-card-balance {
  background: linear-gradient(135deg, #f0f4f9 0%, #e1eaf5 100%);
}

.summary-card-budget {
  background: linear-gradient(135deg, #f6f8f0 0%, #edf2e1 100%);
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
  margin-top: 16px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.recent-list-card {
  padding: 24px;
}

.transaction-list {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transaction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 12px;
  background: #f8fafb;
  transition: transform 0.2s;
}

.transaction-item:hover {
  transform: translateX(4px);
  background: #f1f4f6;
}

.tx-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tx-date {
  font-size: 12px;
  color: #8fa1b0;
}

.tx-category {
  font-size: 14px;
  font-weight: 600;
  color: #34495e;
}

.tx-amount {
  font-weight: 700;
  font-size: 15px;
}

.tx-amount.income { color: #1f8f5f; }
.tx-amount.expense { color: #d04d48; }

.budget-health-shell {
  padding: 24px;
}

.budget-health-list {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.budget-health-item {
  padding: 16px;
  border-radius: 16px;
  background: #f9fbfd;
  border: 1px solid #e4ebf2;
}

.budget-topline {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.budget-inline-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #66788a;
  margin-top: 4px;
}

.budget-status-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.budget-status-pill {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.budget-health-safe .budget-status-pill { background: #e6f4ea; color: #1e7e34; }
.budget-health-warning .budget-status-pill { background: #fff3e0; color: #ef6c00; }
.budget-health-over .budget-status-pill { background: #fdecea; color: #d93025; }

.progress-track {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: #e8eef4;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill { height: 100%; transition: width 0.4s ease; }
.progress-fill-safe { background: #1f8f5f; }
.progress-fill-warning { background: #d6a300; }
.progress-fill-over { background: #d04d48; }

.budget-footer {
  font-size: 12px;
  font-weight: 600;
  color: #546575;
}

.ai-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.ai-card {
  padding: 24px;
}

.ai-text {
  margin-top: 16px;
  line-height: 1.8;
  color: #455a64;
}

.ai-warning {
  color: #7d5a3c;
}

.ai-fallback-shell {
  margin-top: 16px;
  padding: 16px;
  border-radius: 16px;
  background: #fffbf0;
  border: 1px solid #ffecb3;
}

.ai-fallback-banner {
  font-size: 12px;
  font-weight: 800;
  color: #b78628;
  margin-bottom: 8px;
  text-transform: uppercase;
}

@media (max-width: 1024px) {
  .hero-panel {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .bottom-grid, .ai-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
