<template>
  <div class="stocks-page">
    <div class="page-header hero-header">
      <div>
        <p class="eyebrow">Market Workspace</p>
        <h1>Watchlist, cached history, fundamentals, and AI context</h1>
        <p>Price history is cached in the backend, fundamentals sync in background jobs, and the UI never waits on yfinance.</p>
      </div>
    </div>

    <div v-if="actionMessage" class="success-msg">{{ actionMessage }}</div>
    <div v-if="actionError" class="error-msg">{{ actionError }}</div>

    <section class="card">
      <div class="section-header">
        <h2>Watchlist Controls</h2>
        <div class="action-group">
          <button class="btn btn-secondary" :disabled="stockStore.syncAllLoading" @click="handleSyncAll">
            {{ stockStore.syncAllLoading ? 'Queueing...' : 'Queue Price Sync' }}
          </button>
          <button class="btn btn-secondary" :disabled="stockStore.fundamentalsSyncing" @click="handleSyncFundamentals">
            {{ stockStore.fundamentalsSyncing ? 'Queueing...' : 'Queue Fundamentals Sync' }}
          </button>
        </div>
      </div>

      <form class="form-row" @submit.prevent="handleAddWatchlist">
        <div class="form-group">
          <label for="stock-code">Stock Code</label>
          <input id="stock-code" v-model.trim="newStockCode" type="text" placeholder="2330 or AAPL" required />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="isAdding">
          {{ isAdding ? 'Adding...' : 'Add to Watchlist' }}
        </button>
      </form>
    </section>

    <OnboardingCard
      v-if="!stockStore.watchlist.length && !stockStore.dashboardLoading"
      title="Build your market dashboard"
      description="The stock workspace is strongest when price history, fundamentals, and AI explanation all refer to the same selected symbol."
      :steps="[
        'Add a stock code to the watchlist.',
        'Queue price sync to populate historical trend data.',
        'Queue fundamentals sync and review the AI explanation panel.'
      ]"
    />

    <section v-if="stockStore.watchlist.length" class="card stock-selector">
      <h2>Selected Stock</h2>
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
          title="Price Trend"
          subtitle="Cached price history from stock_price_history"
          :loading="stockStore.dashboardLoading"
          :error="stockStore.watchlistError || ''"
          :labels="priceTrend.labels"
          :datasets="priceTrend.datasets"
        />

        <section class="card fundamentals-card">
          <h2>Fundamentals Summary</h2>
          <div v-if="!stockStore.dashboard?.fundamentals" class="empty-state">No data yet</div>
          <div v-else class="fundamentals-grid">
            <article v-for="item in fundamentalsItems" :key="item.label" class="fundamentals-item">
              <span class="fundamentals-label">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </article>
          </div>
        </section>

        <section class="card ai-card">
          <h2>AI Explanation Panel</h2>
          <div v-if="stockStore.dashboard?.ai_explanation" class="ai-explanation">{{ stockStore.dashboard.ai_explanation }}</div>
          <div v-else class="empty-state">No data yet</div>
        </section>
      </div>

      <section class="card">
        <div class="section-header">
          <h2>Watchlist Grid</h2>
          <span class="helper-text">Queued syncs update the status badge without blocking the request.</span>
        </div>

        <div v-if="stockStore.watchlist.length === 0" class="empty-state">No data yet</div>
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
            <div class="tile-price">{{ item.price != null ? formatPrice(item.price) : 'No data yet' }}</div>
            <div class="tile-meta">{{ item.date || 'Awaiting price history' }}</div>
            <div class="tile-actions">
              <button class="btn btn-primary" :disabled="stockStore.isSingleSyncing(item.stock_code)" @click="handleSyncSingle(item.stock_code)">
                {{ stockStore.isSingleSyncing(item.stock_code) ? 'Queueing...' : 'Queue Sync' }}
              </button>
              <button class="btn btn-danger" :disabled="stockStore.deleting" @click="handleDeleteWatchlist(item.id)">Delete</button>
            </div>
            <div v-if="item.last_sync_error" class="tile-error">{{ item.last_sync_error }}</div>
          </article>
        </div>
      </section>

      <div class="stocks-grid">
        <section class="card">
          <h2>Passed Screen</h2>
          <div v-if="stockStore.filterLoading" class="loading-text">Loading screening results...</div>
          <div v-else-if="stockStore.filterError" class="error-msg">{{ stockStore.filterError }}</div>
          <div v-else-if="stockStore.passedStocks.length === 0" class="empty-state">No data yet</div>
          <ul v-else class="result-list">
            <li v-for="stock in stockStore.passedStocks" :key="stock.stock_code">
              <strong>{{ stock.stock_code }}</strong>
              <span>{{ fundamentalsMetaText(stock) }}</span>
            </li>
          </ul>
        </section>

        <section class="card">
          <h2>Needs Attention</h2>
          <div v-if="stockStore.filterLoading" class="loading-text">Loading screening results...</div>
          <div v-else-if="stockStore.filterError" class="error-msg">{{ stockStore.filterError }}</div>
          <div v-else-if="stockStore.failedStocks.length === 0" class="empty-state">No data yet</div>
          <ul v-else class="result-list">
            <li v-for="stock in stockStore.failedStocks" :key="stock.stock_code">
              <strong>{{ stock.stock_code }}</strong>
              <span>{{ stock.fail_reasons.join(' / ') }}</span>
            </li>
          </ul>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ChartPanel from '@/components/ChartPanel.vue'
import OnboardingCard from '@/components/OnboardingCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import { useStockStore } from '@/stores/stockStore'

const stockStore = useStockStore()
const newStockCode = ref('')
const isAdding = ref(false)
const actionMessage = ref('')
const actionError = ref('')

function formatPrice(value) {
  return `NT$ ${Number(value).toLocaleString('zh-TW', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function statusBadgeClass(status) {
  if (status === 'success') return 'badge-success'
  if (status === 'failed') return 'badge-danger'
  return 'badge-warning'
}

function fundamentalsMetaText(stock) {
  const meta = stock?.meta
  if (!meta) return 'No data yet'
  return `${meta.provider} | ttl ${meta.ttl_hours}h | ${meta.is_stale ? 'stale' : 'fresh'}`
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

const fundamentalsItems = computed(() => {
  const fundamentals = stockStore.dashboard?.fundamentals
  if (!fundamentals) return []
  return [
    { label: 'P/E', value: fundamentals.pe_ratio != null ? fundamentals.pe_ratio.toFixed(2) : 'No data yet' },
    { label: 'P/B', value: fundamentals.pb_ratio != null ? fundamentals.pb_ratio.toFixed(2) : 'No data yet' },
    { label: 'Yield', value: fundamentals.dividend_yield != null ? `${fundamentals.dividend_yield.toFixed(2)}%` : 'No data yet' },
    { label: 'Revenue Growth', value: fundamentals.revenue_growth != null ? `${fundamentals.revenue_growth.toFixed(2)}%` : 'No data yet' },
    { label: 'EPS', value: fundamentals.eps != null ? fundamentals.eps.toFixed(2) : 'No data yet' },
    { label: 'Status', value: fundamentals.status || 'No data yet' }
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
    actionMessage.value = `${response.stock_code} added. Market data sync has been queued in the background.`
    await stockStore.fetchFilterResults()
  } catch (error) {
    actionError.value = error.message || 'Unable to add stock.'
  } finally {
    isAdding.value = false
  }
}

async function handleDeleteWatchlist(id) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.deleteFromWatchlist(id)
    actionMessage.value = 'Watchlist item deleted.'
    await stockStore.fetchFilterResults()
  } catch (error) {
    actionError.value = error.message || 'Unable to delete stock.'
  }
}

async function handleSyncSingle(stockCode) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    const response = await stockStore.syncSinglePrice(stockCode)
    actionMessage.value = response?.message || `${stockCode} sync queued.`
  } catch (error) {
    actionError.value = error.message || `Unable to sync ${stockCode}.`
  }
}

async function handleSyncAll() {
  actionMessage.value = ''
  actionError.value = ''
  try {
    const response = await stockStore.syncAllPrices()
    actionMessage.value = response.message || 'Watchlist sync queued.'
  } catch (error) {
    actionError.value = error.message || 'Unable to sync watchlist prices.'
  }
}

async function handleSyncFundamentals() {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.syncFundamentals()
    actionMessage.value = 'Fundamentals sync queued for watchlist items.'
  } catch (error) {
    actionError.value = error.message || 'Unable to sync fundamentals.'
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
