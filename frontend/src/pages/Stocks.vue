<template>
  <div class="stocks-page">
    <div class="page-header hero-header">
      <div>
        <p class="eyebrow">{{ t('stocks.heroTag') }}</p>
        <h1>{{ t('stocks.heroTitle') }}</h1>
        <p>{{ t('stocks.heroSubtitle') }}</p>
      </div>
    </div>

    <div v-if="actionMessage" class="success-msg">{{ actionMessage }}</div>
    <div v-if="actionError" class="error-msg">{{ actionError }}</div>

    <section class="card">
      <div class="section-header">
        <h2>{{ t('stocks.controls') }}</h2>
        <div class="action-group">
          <button class="btn btn-secondary" :disabled="stockStore.syncAllLoading" @click="handleSyncAll">
            {{ stockStore.syncAllLoading ? t('stocks.queueing') : t('stocks.queuePriceSync') }}
          </button>
          <button class="btn btn-secondary" :disabled="stockStore.fundamentalsSyncing" @click="handleSyncFundamentals">
            {{ stockStore.fundamentalsSyncing ? t('stocks.queueing') : t('stocks.queueFundamentalsSync') }}
          </button>
        </div>
      </div>

      <form class="form-row" @submit.prevent="handleAddWatchlist">
        <div class="form-group">
          <label for="stock-code">{{ t('stocks.stockCode') }}</label>
          <input id="stock-code" v-model.trim="newStockCode" type="text" placeholder="2330 or AAPL" required />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="isAdding">
          {{ isAdding ? t('stocks.adding') : t('stocks.addWatchlist') }}
        </button>
      </form>
    </section>

    <OnboardingCard
      v-if="!stockStore.watchlist.length && !stockStore.dashboardLoading"
      :title="t('stocks.onboardingTitle')"
      :description="t('stocks.onboardingDescription')"
      :steps="[
        t('stocks.onboardingStepOne'),
        t('stocks.onboardingStepTwo'),
        t('stocks.onboardingStepThree')
      ]"
    />

    <section v-if="stockStore.watchlist.length" class="card stock-selector">
      <h2>{{ t('stocks.selectedStock') }}</h2>
      <div class="chip-list">
        <button
          v-for="item in stockStore.watchlist"
          :key="item.id"
          class="stock-chip"
          :class="{ active: item.stock_code === stockStore.selectedStockCode }"
          @click="handleSelectStock(item.stock_code)"
        >
          {{ item.stock_code }}
        </button>
      </div>
    </section>

    <div v-if="stockStore.dashboardLoading" class="stocks-grid">
      <SkeletonCard v-for="index in 3" :key="index" />
    </div>
    <div v-else-if="stockStore.watchlistError" class="error-msg">{{ stockStore.watchlistError }}</div>

    <template v-else>
      <div class="stocks-grid">
        <ChartPanel
          :title="t('stocks.priceTrend')"
          :subtitle="t('stocks.priceTrendSubtitle')"
          :loading="stockStore.dashboardLoading"
          :error="stockStore.watchlistError || ''"
          :labels="priceTrend.labels"
          :datasets="priceTrend.datasets"
        />

        <section class="card fundamentals-card">
          <h2>{{ t('stocks.fundamentalsSummary') }}</h2>
          <div v-if="!stockStore.dashboard?.fundamentals" class="empty-state">{{ t('common.empty') }}</div>
          <div v-else class="fundamentals-grid">
            <article v-for="item in fundamentalsItems" :key="item.label" class="fundamentals-item">
              <span class="fundamentals-label">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </article>
          </div>
        </section>

        <section class="card ai-card">
          <h2>{{ t('stocks.aiExplanation') }}</h2>
          <template v-if="aiExplanation">
            <div v-if="aiExplanation.status === 'ready' && aiExplanation.explanation" class="ai-explanation">
              {{ aiExplanation.explanation }}
            </div>
            <div v-else class="ai-status-panel">
              <p class="ai-status-message">{{ aiExplanationDisplayMessage }}</p>
              <div class="ai-status-actions">
                <button
                  v-if="aiExplanation.can_sync && aiExplanation.status === 'sync_required'"
                  class="btn btn-primary"
                  :disabled="stockStore.isSingleFundamentalsSyncing(stockStore.selectedStockCode)"
                  @click="handleSyncSelectedFundamentals"
                >
                  {{
                    stockStore.isSingleFundamentalsSyncing(stockStore.selectedStockCode)
                      ? t('stocks.queueing')
                      : t('stocks.ai.syncFundamentals')
                  }}
                </button>
                <button
                  v-if="aiExplanation.status === 'sync_queued'"
                  class="btn btn-secondary"
                  @click="handleRetryExplanation"
                >
                  {{ t('stocks.ai.retryExplanation') }}
                </button>
              </div>
            </div>
          </template>
          <div v-else class="empty-state">{{ t('stocks.ai.explanationUnavailable') }}</div>
        </section>
      </div>

      <section class="card">
        <div class="section-header">
          <h2>{{ t('stocks.watchlistGrid') }}</h2>
          <span class="helper-text">{{ t('stocks.helperText') }}</span>
        </div>

        <div v-if="stockStore.watchlist.length === 0" class="empty-state">{{ t('common.empty') }}</div>
        <div v-else class="watchlist-grid">
          <article v-for="item in stockStore.watchlist" :key="item.id" class="watchlist-tile">
            <div class="tile-head">
              <div>
                <strong>{{ item.stock_code }}</strong>
                <div class="tile-name">{{ item.name || item.stock_code }}</div>
              </div>
              <span class="badge" :class="statusBadgeClass(item.price_sync_status)">
                {{ item.price_sync_status }}
              </span>
            </div>
            <div class="tile-price">{{ item.price != null ? formatPrice(item.price) : t('stocks.noDataPrice') }}</div>
            <div class="tile-meta">{{ item.date || t('stocks.awaitingPriceHistory') }}</div>
            <div class="tile-actions">
              <button class="btn btn-primary" :disabled="stockStore.isSingleSyncing(item.stock_code)" @click="handleSyncSingle(item.stock_code)">
                {{ stockStore.isSingleSyncing(item.stock_code) ? t('stocks.queueing') : t('stocks.queuePriceSync') }}
              </button>
              <button class="btn btn-danger" :disabled="stockStore.deleting" @click="handleDeleteWatchlist(item.id)">{{ t('common.delete') }}</button>
            </div>
            <div v-if="item.last_sync_error" class="tile-error">{{ item.last_sync_error }}</div>
          </article>
        </div>
      </section>

      <div class="stocks-grid">
        <section class="card">
          <h2>{{ t('stocks.passedScreen') }}</h2>
          <div v-if="stockStore.filterLoading" class="loading-text">{{ t('stocks.loadingScreening') }}</div>
          <div v-else-if="stockStore.filterError" class="error-msg">{{ stockStore.filterError }}</div>
          <div v-else-if="stockStore.passedStocks.length === 0" class="empty-state">{{ t('common.empty') }}</div>
          <ul v-else class="result-list">
            <li v-for="stock in stockStore.passedStocks" :key="stock.stock_code">
              <strong>{{ stock.stock_code }}</strong>
              <span>{{ fundamentalsMetaText(stock) }}</span>
            </li>
          </ul>
        </section>

        <section class="card">
          <h2>{{ t('stocks.needsAttention') }}</h2>
          <div v-if="stockStore.filterLoading" class="loading-text">{{ t('stocks.loadingScreening') }}</div>
          <div v-else-if="stockStore.filterError" class="error-msg">{{ stockStore.filterError }}</div>
          <div v-else-if="stockStore.failedStocks.length === 0" class="empty-state">{{ t('common.empty') }}</div>
          <ul v-else class="result-list">
            <li v-for="stock in stockStore.failedStocks" :key="stock.stock_code">
              <strong>{{ stock.stock_code }}</strong>
              <span>{{ screeningMessage(stock) }}</span>
            </li>
          </ul>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ChartPanel from '@/components/ChartPanel.vue'
import OnboardingCard from '@/components/OnboardingCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import { useStockStore } from '@/stores/stockStore'
import { formatCurrency as formatCurrencyValue } from '@/utils/formatters'

const stockStore = useStockStore()
const newStockCode = ref('')
const isAdding = ref(false)
const actionMessage = ref('')
const actionError = ref('')
const { t, locale } = useI18n()

function formatPrice(value) {
  return formatCurrencyValue(Number(value), locale.value)
}

function statusBadgeClass(status) {
  if (status === 'success') return 'badge-success'
  if (status === 'failed') return 'badge-danger'
  return 'badge-warning'
}

function fundamentalsMetaText(stock) {
  const meta = stock?.meta
  if (!meta) return t('common.empty')
  return `${meta.provider} | ttl ${meta.ttl_hours}h | ${meta.is_stale ? t('stocks.stale') : t('stocks.fresh')}`
}

function screeningMessage(stock) {
  const status = stock?.meta?.status
  if (status === 'sync_required' || (!stock?.fundamentals && !status)) {
    return t('stocks.ai.syncRequired', { stockCode: stock.stock_code })
  }
  if (status === 'pending') {
    return t('stocks.ai.syncQueued')
  }
  if (status === 'unsupported') {
    return t('stocks.ai.unsupported')
  }
  return stock?.fail_reasons?.join(' / ') || t('stocks.ai.explanationUnavailable')
}

const priceTrend = computed(() => ({
  labels: stockStore.dashboard?.price_history?.map((item) => item.trade_date) || [],
  datasets: [
    {
      label: stockStore.selectedStockCode || 'Price',
      data: stockStore.dashboard?.price_history?.map((item) => item.close) || [],
      borderColor: '#102b44',
      backgroundColor: 'rgba(16, 43, 68, 0.14)',
      fill: true,
      tension: 0.3
    }
  ]
}))

const aiExplanation = computed(() => stockStore.dashboard?.ai_explanation || null)

const aiExplanationDisplayMessage = computed(() => {
  const payload = aiExplanation.value
  if (!payload) return t('stocks.ai.explanationUnavailable')
  if (payload.status === 'sync_required') {
    return t('stocks.ai.syncRequired', { stockCode: payload.stock_code || stockStore.selectedStockCode || '' })
  }
  if (payload.status === 'sync_queued') {
    return t('stocks.ai.syncQueued')
  }
  if (payload.status === 'unsupported') {
    return t('stocks.ai.unsupported')
  }
  return payload.message || t('stocks.ai.explanationUnavailable')
})

const fundamentalsItems = computed(() => {
  const fundamentals = stockStore.dashboard?.fundamentals
  if (!fundamentals) return []
  return [
    { label: 'P/E', value: fundamentals.pe_ratio != null ? fundamentals.pe_ratio.toFixed(2) : t('common.empty') },
    { label: 'P/B', value: fundamentals.pb_ratio != null ? fundamentals.pb_ratio.toFixed(2) : t('common.empty') },
    { label: 'Yield', value: fundamentals.dividend_yield != null ? `${fundamentals.dividend_yield.toFixed(2)}%` : t('common.empty') },
    { label: 'Revenue Growth', value: fundamentals.revenue_growth != null ? `${fundamentals.revenue_growth.toFixed(2)}%` : t('common.empty') },
    { label: 'EPS', value: fundamentals.eps != null ? fundamentals.eps.toFixed(2) : t('common.empty') },
    { label: 'Status', value: fundamentals.status || t('common.empty') }
  ]
})

async function refreshStockWorkspace(selectedCode = null) {
  await Promise.all([
    stockStore.fetchDashboard(selectedCode),
    stockStore.fetchFilterResults()
  ])
}

async function handleAddWatchlist() {
  if (!newStockCode.value) return
  isAdding.value = true
  actionMessage.value = ''
  actionError.value = ''

  try {
    const response = await stockStore.addToWatchlist(newStockCode.value)
    newStockCode.value = ''
    actionMessage.value = `${response.stock_code} ${t('stocks.syncQueued')}`
    await stockStore.fetchFilterResults()
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  } finally {
    isAdding.value = false
  }
}

async function handleDeleteWatchlist(id) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.deleteFromWatchlist(id)
    actionMessage.value = t('common.delete')
    await stockStore.fetchFilterResults()
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleSyncSingle(stockCode) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    const response = await stockStore.syncSinglePrice(stockCode)
    actionMessage.value = response?.message || `${stockCode} ${t('stocks.syncQueued')}`
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleSyncAll() {
  actionMessage.value = ''
  actionError.value = ''
  try {
    const response = await stockStore.syncAllPrices()
    actionMessage.value = response.message || 'Watchlist sync queued.'
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleSyncFundamentals() {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.syncFundamentals()
    actionMessage.value = t('stocks.syncQueued')
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleSyncSelectedFundamentals() {
  if (!stockStore.selectedStockCode) return
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.syncSingleFundamentals(stockStore.selectedStockCode)
    actionMessage.value = t('stocks.ai.syncQueued')
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleRetryExplanation() {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await refreshStockWorkspace(stockStore.selectedStockCode)
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleSelectStock(stockCode) {
  await stockStore.fetchDashboard(stockCode)
}

onMounted(() => {
  refreshStockWorkspace()
})
</script>

<style scoped>
.stocks-page {
  display: grid;
  gap: 20px;
}

.hero-header {
  padding: 24px 28px;
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(207, 92, 54, 0.26), transparent 28%),
    linear-gradient(135deg, #143049 0%, #1f4765 50%, #2d6b77 100%);
  color: #f8fbff;
}

.eyebrow {
  margin: 0 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 12px;
  color: rgba(255, 231, 202, 0.95);
}

.section-header,
.action-group,
.tile-actions,
.tile-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header,
.tile-head {
  justify-content: space-between;
}

.stock-selector {
  display: grid;
  gap: 12px;
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stock-chip {
  border: 1px solid #cfdae5;
  background: #f6fafc;
  border-radius: 999px;
  padding: 10px 16px;
  font-weight: 700;
  cursor: pointer;
}

.stock-chip.active {
  border-color: #102b44;
  background: #102b44;
  color: #fff;
}

.stocks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.watchlist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.watchlist-tile {
  border: 1px solid #e1eaf2;
  border-radius: 16px;
  padding: 16px;
  background: linear-gradient(180deg, #fff 0%, #f7fbfd 100%);
}

.tile-name,
.tile-meta,
.helper-text,
.fundamentals-label {
  color: #66788a;
}

.tile-price {
  margin: 14px 0 6px;
  font-size: 26px;
  font-weight: 700;
  color: #102b44;
}

.tile-actions {
  margin-top: 14px;
}

.tile-error {
  margin-top: 10px;
  color: #9a2c2c;
  font-size: 12px;
}

.fundamentals-card,
.ai-card {
  min-height: 340px;
}

.fundamentals-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.fundamentals-item {
  padding: 14px;
  border-radius: 14px;
  background: #f5f8fb;
  display: grid;
  gap: 8px;
}

.ai-explanation {
  white-space: pre-line;
  line-height: 1.7;
  padding: 14px 16px;
  border-radius: 14px;
  background: #f5f8fb;
  border-left: 4px solid #cf5c36;
}

.ai-status-panel {
  display: grid;
  gap: 16px;
  padding: 16px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e1eaf2;
}

.ai-status-message {
  margin: 0;
  color: #445767;
  line-height: 1.7;
}

.ai-status-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.result-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 12px;
}

.result-list li {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 14px;
  background: #f7fafc;
}
</style>
