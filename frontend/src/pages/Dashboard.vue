<template>
  <div class="dashboard-page">
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
          <strong>{{ formatCurrency(monthlyNetBalance) }}</strong>
          <p>{{ monthlyNetBalance >= 0 ? t('dashboard.summary.balanceNote') : t('dashboard.statusBudgetTight') }}</p>
        </article>
        <article class="hero-status-card">
          <span class="status-label">{{ t('dashboard.statusBudget') }}</span>
          <strong>{{ budgetHealthLabel }}</strong>
          <p>{{ formatPercent(topBudgetUsagePercent) }}</p>
        </article>
        <article class="hero-status-card">
          <span class="status-label">{{ t('dashboard.statusAi') }}</span>
          <strong>{{ aiStatusLabel }}</strong>
          <p>{{ aiStatusDescription }}</p>
        </article>
      </div>
    </section>

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
          <span class="summary-status">{{ item.status }}</span>
        </div>
        <div class="card-label">{{ item.title }}</div>
        <div class="stat-value" :class="item.valueClass">{{ item.value }}</div>
        <div class="card-note">{{ item.note }}</div>
      </section>
    </div>

    <div v-if="store.error && !store.summary" class="error-msg">{{ store.error }}</div>

    <section class="insight-section">
      <div class="section-copy">
        <h2>{{ t('nav.dashboard') }}</h2>
        <p>{{ t('dashboard.insight.netIncomeTrendSubtitle') }}</p>
      </div>

      <div class="insight-grid">
        <ChartPanel
          :title="t('dashboard.insight.expenseTrend')"
          :subtitle="t('dashboard.insight.expenseTrendSubtitle')"
          :loading="store.chartsLoading"
          :error="store.chartsError || ''"
          :labels="expenseTrend.labels"
          :datasets="expenseTrend.datasets"
        />
        <ChartPanel
          :title="t('dashboard.insight.categoryDistribution')"
          :subtitle="t('dashboard.insight.categoryDistributionSubtitle')"
          type="pie"
          :loading="store.chartsLoading"
          :error="store.chartsError || ''"
          :labels="categoryDistribution.labels"
          :datasets="categoryDistribution.datasets"
        />
        <ChartPanel
          :title="t('dashboard.insight.netIncomeTrend')"
          :subtitle="t('dashboard.insight.netIncomeTrendSubtitle')"
          :loading="store.chartsLoading"
          :error="store.chartsError || ''"
          :labels="netIncomeTrend.labels"
          :datasets="netIncomeTrend.datasets"
        />
      </div>
    </section>

    <section class="budget-health-shell card">
      <div class="section-heading">
        <div>
          <h2>{{ t('dashboard.budgetHealth.title') }}</h2>
          <p>{{ t('dashboard.budgetHealth.subtitle') }}</p>
        </div>
      </div>

      <div v-if="store.chartsLoading" class="budget-skeleton-list">
        <div v-for="index in 4" :key="index" class="budget-skeleton-row" />
      </div>
      <div v-else-if="store.chartsError && !budgetUsage.length" class="empty-budget-state">
        <div class="budget-empty-visual" />
        <strong>{{ t('dashboard.empty.budgetTitle') }}</strong>
        <p>{{ t('dashboard.empty.budgetDescription') }}</p>
      </div>
      <div v-else-if="!budgetUsage.length" class="empty-budget-state">
        <div class="budget-empty-visual" />
        <strong>{{ t('dashboard.empty.budgetTitle') }}</strong>
        <p>{{ t('dashboard.empty.budgetDescription') }}</p>
      </div>
      <div v-else class="budget-health-list">
        <article
          v-for="item in budgetUsage"
          :key="item.category"
          class="budget-health-item"
          :class="`budget-health-${budgetStatus(item.percent_used).tone}`"
        >
          <div class="budget-topline">
            <div>
              <strong>{{ translateCategory(t, item.category) }}</strong>
              <div class="budget-inline-meta">
                <span>{{ t('dashboard.budgetHealth.spent') }} {{ formatCurrency(item.current_spent) }}</span>
                <span>{{ t('dashboard.budgetHealth.limit') }} {{ formatCurrency(item.monthly_limit) }}</span>
              </div>
            </div>
            <div class="budget-status-meta">
              <span class="budget-status-pill">{{ budgetStatus(item.percent_used).label }}</span>
              <strong>{{ formatPercent(item.percent_used) }}</strong>
            </div>
          </div>

          <div class="progress-track">
            <div
              class="progress-fill"
              :class="`progress-fill-${budgetStatus(item.percent_used).tone}`"
              :style="{ width: `${Math.min(item.percent_used, 100)}%` }"
            />
          </div>

          <div class="budget-footer">
            <span v-if="item.percent_used > 100">
              {{ t('dashboard.budgetHealth.overBy') }} {{ formatCurrency(item.current_spent - item.monthly_limit) }}
            </span>
            <span v-else>
              {{ t('dashboard.budgetHealth.remaining') }} {{ formatCurrency(item.monthly_limit - item.current_spent) }}
            </span>
          </div>
        </article>
      </div>
    </section>

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

function budgetStatus(percentUsed) {
  if (percentUsed > 100) {
    return { tone: 'danger', label: t('dashboard.budgetHealth.danger') }
  }
  if (percentUsed >= 80) {
    return { tone: 'warning', label: t('dashboard.budgetHealth.warning') }
  }
  return { tone: 'healthy', label: t('dashboard.budgetHealth.healthy') }
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
      label: t('dashboard.summary.expense'),
      data: store.charts?.monthly_expense_trend?.map((item) => item.expense) || [],
      borderColor: '#ca7a54',
      backgroundColor: 'rgba(226, 179, 150, 0.32)',
      fill: true,
      tension: 0.36
    }
  ]
}))

const categoryDistribution = computed(() => ({
  labels: store.charts?.category_distribution?.map((item) => translateCategory(t, item.category)) || [],
  datasets: [
    {
      data: store.charts?.category_distribution?.map((item) => item.amount) || [],
      backgroundColor: ['#27556f', '#dd9f73', '#75a68f', '#8aa6c1', '#d4c1a5', '#b9d4cf']
    }
  ]
}))

const netIncomeTrend = computed(() => ({
  labels: store.charts?.net_income_trend?.map((item) => item.month) || [],
  datasets: [
    {
      label: t('dashboard.summary.income'),
      data: store.charts?.net_income_trend?.map((item) => item.income) || [],
      borderColor: '#2f7a76',
      backgroundColor: 'rgba(130, 201, 188, 0.24)',
      tension: 0.32
    },
    {
      label: t('dashboard.summary.expense'),
      data: store.charts?.net_income_trend?.map((item) => item.expense) || [],
      borderColor: '#25465b',
      backgroundColor: 'rgba(157, 180, 197, 0.16)',
      tension: 0.32
    }
  ]
}))

const budgetUsage = computed(() =>
  [...(store.charts?.budget_usage || [])].sort((a, b) => b.percent_used - a.percent_used)
)

const budgetUsagePercent = computed(() => {
  const totalLimit = budgetUsage.value.reduce((sum, item) => sum + Number(item.monthly_limit || 0), 0)
  const totalSpent = budgetUsage.value.reduce((sum, item) => sum + Number(item.current_spent || 0), 0)
  if (!totalLimit) return 0
  return (totalSpent / totalLimit) * 100
})

const topBudgetUsagePercent = computed(() => budgetUsage.value[0]?.percent_used || 0)

const latestTrendPoint = computed(() => {
  const trend = store.charts?.net_income_trend || []
  return trend[trend.length - 1] || null
})

const monthlyNetBalance = computed(() => {
  if (!latestTrendPoint.value) {
    return Number(store.summary?.net_balance || 0)
  }
  return Number(latestTrendPoint.value.income || 0) - Number(latestTrendPoint.value.expense || 0)
})

const budgetHealthLabel = computed(() => budgetStatus(topBudgetUsagePercent.value).label)

const aiStatusLabel = computed(() => (
  store.aiSummaryError || store.budgetAdviceError ? t('dashboard.statusAiFallback') : t('dashboard.statusAiReady')
))

const aiStatusDescription = computed(() => {
  if (store.aiSummaryError || store.budgetAdviceError) {
    return t('dashboard.ai.fallbackDescription')
  }
  return budgetUsage.value.length ? `${t('dashboard.budgetHealth.title')} ${formatPercent(budgetUsagePercent.value)}` : t('dashboard.statusAiReady')
})

const statCards = computed(() => [
  {
    key: 'income',
    icon: '+',
    tone: 'income',
    title: t('dashboard.summary.income'),
    value: formatCurrency(store.summary?.total_income || 0),
    note: t('dashboard.summary.incomeNote'),
    status: t('dashboard.budgetHealth.healthy'),
    valueClass: 'income'
  },
  {
    key: 'expense',
    icon: '-',
    tone: 'expense',
    title: t('dashboard.summary.expense'),
    value: formatCurrency(store.summary?.total_expense || 0),
    note: t('dashboard.summary.expenseNote'),
    status: budgetUsage.value.some((item) => item.percent_used > 100) ? t('dashboard.budgetHealth.danger') : t('dashboard.budgetHealth.warning'),
    valueClass: 'expense'
  },
  {
    key: 'balance',
    icon: '=',
    tone: 'balance',
    title: t('dashboard.summary.netBalance'),
    value: formatCurrency(store.summary?.net_balance || 0),
    note: t('dashboard.summary.balanceNote'),
    status: (store.summary?.net_balance || 0) >= 0 ? t('dashboard.budgetHealth.healthy') : t('dashboard.statusBudgetTight'),
    valueClass: (store.summary?.net_balance || 0) >= 0 ? 'income' : 'expense'
  },
  {
    key: 'budget',
    icon: '%',
    tone: 'budget',
    title: t('dashboard.summary.budgetUsage'),
    value: formatPercent(budgetUsagePercent.value),
    note: t('dashboard.summary.budgetUsageNote'),
    status: budgetStatus(budgetUsagePercent.value).label,
    valueClass: budgetStatus(budgetUsagePercent.value).tone === 'danger' ? 'expense' : 'balance'
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
    const status = budgetStatus(topBudget.percent_used).label
    return {
      text: `${t('dashboard.ai.fallbackAdviceDefault')} ${translateCategory(t, topBudget.category)} ${status}，${formatPercent(topBudget.percent_used)}。`,
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
  store.fetchCharts()
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
  min-height: 182px;
}

.summary-card::after {
  content: '';
  position: absolute;
  right: -28px;
  bottom: -30px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  opacity: 0.18;
}

.summary-card-income::after {
  background: #86cfb8;
}

.summary-card-expense::after {
  background: #efc09e;
}

.summary-card-balance::after {
  background: #a7c3df;
}

.summary-card-budget::after {
  background: #c8d8a6;
}

.summary-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.summary-icon {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 18px;
  font-weight: 800;
  color: #204050;
  background: rgba(241, 247, 248, 0.98);
  border: 1px solid rgba(216, 227, 233, 0.9);
}

.summary-status {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: #617482;
  font-size: 12px;
  font-weight: 700;
}

.card-label {
  margin-top: 18px;
  color: #627585;
}

.card-note {
  margin-top: 10px;
  max-width: 250px;
  color: #6b7c89;
  font-size: 13px;
  line-height: 1.7;
}

.insight-section {
  display: grid;
  gap: 16px;
}

.section-copy h2 {
  margin: 0;
  font-size: 24px;
  color: #1f3442;
}

.section-copy p {
  margin: 8px 0 0;
  color: #677a88;
  line-height: 1.7;
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.budget-health-shell {
  display: grid;
  gap: 18px;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.section-heading p {
  margin: 8px 0 0;
  color: #6b7d8b;
  line-height: 1.7;
}

.budget-health-list {
  display: grid;
  gap: 14px;
}

.budget-health-item {
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(221, 230, 235, 0.92);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 250, 252, 0.94));
}

.budget-health-healthy {
  border-color: rgba(180, 224, 203, 0.92);
}

.budget-health-warning {
  border-color: rgba(241, 208, 150, 0.94);
}

.budget-health-danger {
  border-color: rgba(236, 188, 172, 0.96);
}

.budget-topline,
.budget-inline-meta,
.budget-status-meta,
.budget-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.budget-topline {
  align-items: flex-start;
}

.budget-inline-meta {
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-top: 8px;
  color: #6e7f8d;
  font-size: 13px;
}

.budget-status-meta {
  flex-direction: column;
  align-items: flex-end;
}

.budget-status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(243, 247, 249, 0.92);
  color: #5f7280;
  font-size: 12px;
  font-weight: 700;
}

.progress-track {
  width: 100%;
  height: 12px;
  margin-top: 14px;
  border-radius: 999px;
  background: #ebf0f3;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
}

.progress-fill-healthy {
  background: linear-gradient(90deg, #64b88e, #2f7a76);
}

.progress-fill-warning {
  background: linear-gradient(90deg, #f1c16f, #da8c43);
}

.progress-fill-danger {
  background: linear-gradient(90deg, #e58c73, #ce6258);
}

.budget-footer {
  margin-top: 12px;
  color: #60727f;
  font-size: 13px;
}

.budget-skeleton-list {
  display: grid;
  gap: 14px;
}

.budget-skeleton-row {
  height: 92px;
  border-radius: 20px;
  background: linear-gradient(90deg, rgba(228, 235, 240, 0.7), rgba(248, 250, 252, 0.95), rgba(228, 235, 240, 0.7));
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.empty-budget-state {
  display: grid;
  place-items: center;
  gap: 10px;
  min-height: 180px;
  text-align: center;
  padding: 18px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(248, 250, 246, 0.96), rgba(241, 246, 249, 0.98));
  border: 1px dashed rgba(178, 193, 203, 0.52);
}

.empty-budget-state.compact {
  min-height: 160px;
}

.empty-budget-state strong {
  color: #243a48;
}

.empty-budget-state p {
  margin: 0;
  max-width: 360px;
  color: #677987;
  line-height: 1.7;
}

.budget-empty-visual {
  width: 72px;
  height: 72px;
  border-radius: 24px;
  background:
    radial-gradient(circle at 50% 26%, rgba(191, 223, 208, 0.84), transparent 28%),
    linear-gradient(135deg, rgba(233, 239, 243, 0.96), rgba(218, 229, 236, 0.86));
  box-shadow: inset 0 0 0 1px rgba(177, 193, 203, 0.44);
}

.ai-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.ai-card {
  display: grid;
  gap: 16px;
}

.ai-fallback-shell {
  display: grid;
  gap: 12px;
}

.ai-fallback-banner {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(248, 242, 232, 0.92);
  border: 1px solid rgba(234, 213, 179, 0.9);
  color: #87674a;
  font-size: 13px;
  line-height: 1.6;
}

.ai-text {
  margin: 0;
  padding: 16px;
  border-radius: 18px;
  background: rgba(244, 248, 250, 0.96);
  border: 1px solid rgba(223, 231, 236, 0.92);
  line-height: 1.8;
  white-space: pre-line;
  color: #253846;
}

.ai-warning {
  background: rgba(250, 245, 241, 0.96);
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (max-width: 1120px) {
  .stats-grid,
  .insight-grid,
  .ai-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-panel {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .hero-panel {
    padding: 22px;
    border-radius: 26px;
  }

  .stats-grid,
  .insight-grid,
  .ai-grid {
    grid-template-columns: 1fr;
  }

  .hero-status-card strong {
    font-size: 22px;
  }

  .budget-topline,
  .budget-status-meta,
  .budget-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .budget-status-meta {
    align-items: flex-start;
  }
}
</style>
