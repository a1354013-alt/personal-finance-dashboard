<template>
  <div>
    <div class="page-header">
      <h1>Stocks</h1>
      <p>Watchlist price sync states are explicit: success, pending, or failed.</p>
    </div>

    <div v-if="actionMessage" class="success-msg">{{ actionMessage }}</div>
    <div v-if="actionError" class="error-msg">{{ actionError }}</div>

    <section class="card">
      <div class="section-header">
        <h2>Watchlist</h2>
        <button class="btn btn-secondary" :disabled="stockStore.syncAllLoading" @click="handleSyncAll">
          {{ stockStore.syncAllLoading ? 'Syncing...' : 'Sync Prices' }}
        </button>
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

      <div v-if="stockStore.watchlistLoading" class="loading-text">Loading watchlist...</div>
      <div v-else-if="stockStore.watchlistError" class="error-msg">{{ stockStore.watchlistError }}</div>
      <div v-else-if="stockStore.watchlist.length === 0" class="empty-state">No watchlist items yet.</div>

      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Latest Price</th>
              <th>Trade Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in stockStore.watchlist" :key="item.id">
              <td>{{ item.stock_code }}</td>
              <td>{{ item.name || item.stock_code }}</td>
              <td>{{ item.price ? formatPrice(item.price) : '-' }}</td>
              <td>{{ item.date || '-' }}</td>
              <td>
                <span class="badge" :class="statusBadgeClass(item.price_sync_status)">
                  {{ statusLabel(item.price_sync_status) }}
                </span>
                <div v-if="item.last_sync_error" class="status-detail">{{ item.last_sync_error }}</div>
              </td>
              <td>
                <button class="btn btn-danger" @click="handleDeleteWatchlist(item.id)">Delete</button>
                <button
                  class="btn btn-primary row-action-btn"
                  :disabled="stockStore.isSingleSyncing(item.stock_code)"
                  @click="handleSyncSingle(item.stock_code)"
                >
                  {{ stockStore.isSingleSyncing(item.stock_code) ? 'Syncing...' : 'Sync' }}
                </button>
                <div v-if="singleSyncErrors[item.stock_code]" class="status-detail error-inline">
                  {{ singleSyncErrors[item.stock_code] }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card">
      <div class="section-header">
        <h2>Fundamentals Screening</h2>
        <button
          class="btn btn-secondary"
          :disabled="stockStore.fundamentalsSyncing"
          @click="handleSyncFundamentals"
        >
          {{ stockStore.fundamentalsSyncing ? 'Syncing...' : 'Sync Fundamentals' }}
        </button>
      </div>
      <p class="helper-text">
        {{ stockStore.filterMetadata?.message || 'Screening metadata unavailable.' }}
      </p>
      <p class="helper-text" v-if="stockStore.filterMetadata">
        Provider: {{ stockStore.filterMetadata.fundamentals_provider }} · TTL: {{ stockStore.filterMetadata.ttl_hours }}h · Timeout:
        {{ stockStore.filterMetadata.timeout_seconds }}s
      </p>
      <div v-if="stockStore.fundamentalsError" class="error-msg">{{ stockStore.fundamentalsError }}</div>
    </section>

    <div class="stocks-grid">
      <section class="card">
        <h2>Passed</h2>
        <div v-if="stockStore.filterLoading" class="loading-text">Loading screening results...</div>
        <div v-else-if="stockStore.filterError" class="error-msg">{{ stockStore.filterError }}</div>
        <div v-else-if="stockStore.passedStocks.length === 0" class="empty-state">No watchlist items passed the fundamentals screen.</div>
        <ul v-else class="result-list">
          <li v-for="stock in stockStore.passedStocks" :key="stock.stock_code" class="result-item result-pass">
            <strong>{{ stock.stock_code }}</strong>
            <span class="muted">{{ fundamentalsMetaText(stock) }}</span>
            <span class="muted">{{ fundamentalsMetricText(stock) }}</span>
          </li>
        </ul>
      </section>

      <section class="card">
        <h2>Failed</h2>
        <div v-if="stockStore.filterLoading" class="loading-text">Loading screening results...</div>
        <div v-else-if="stockStore.filterError" class="error-msg">{{ stockStore.filterError }}</div>
        <div v-else-if="stockStore.failedStocks.length === 0" class="empty-state">No failed items.</div>
        <ul v-else class="result-list">
          <li v-for="stock in stockStore.failedStocks" :key="stock.stock_code" class="result-item result-fail">
            <strong>{{ stock.stock_code }}</strong>
            <span class="muted">{{ fundamentalsMetaText(stock) }}</span>
            <span class="muted" v-if="stock.fundamentals">{{ fundamentalsMetricText(stock) }}</span>
            <span>{{ stock.fail_reasons.join(' / ') }}</span>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useStockStore } from '@/stores/stockStore'

const stockStore = useStockStore()
const newStockCode = ref('')
const isAdding = ref(false)
const actionMessage = ref('')
const actionError = ref('')
const singleSyncErrors = ref({})

function formatPrice(value) {
  return `NT$ ${Number(value).toLocaleString('zh-TW', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function statusLabel(status) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'failed'
  return 'pending'
}

function statusBadgeClass(status) {
  if (status === 'success') return 'badge-success'
  if (status === 'failed') return 'badge-danger'
  return 'badge-warning'
}

function fundamentalsMetaText(stock) {
  const meta = stock?.meta
  if (!meta) return 'No fundamentals metadata.'
  const status = meta.status ? `status=${meta.status}` : 'status=missing'
  const asOf = meta.as_of_date ? `as_of=${meta.as_of_date}` : 'as_of=-'
  const stale = meta.is_stale ? 'stale' : 'fresh'
  return `${meta.provider} · ${status} · ${asOf} · ${stale}`
}

function fundamentalsMetricText(stock) {
  const f = stock?.fundamentals
  if (!f) return 'No fundamentals cached.'
  const pe = f.pe_ratio != null ? `P/E ${Number(f.pe_ratio).toFixed(2)}` : 'P/E -'
  const pb = f.pb_ratio != null ? `P/B ${Number(f.pb_ratio).toFixed(2)}` : 'P/B -'
  const div = f.dividend_yield != null ? `Yield ${Number(f.dividend_yield).toFixed(2)}%` : 'Yield -'
  const rev = f.revenue_growth != null ? `Rev ${Number(f.revenue_growth).toFixed(2)}%` : 'Rev -'
  const eps = f.eps != null ? `EPS ${Number(f.eps).toFixed(2)}` : 'EPS -'
  return `${pe} · ${pb} · ${div} · ${rev} · ${eps}`
}

async function refreshStocksView() {
  await Promise.all([stockStore.fetchWatchlist(), stockStore.fetchFilterResults()])
}

async function handleAddWatchlist() {
  if (!newStockCode.value) return

  isAdding.value = true
  actionMessage.value = ''
  actionError.value = ''

  try {
    const response = await stockStore.addToWatchlist(newStockCode.value)
    newStockCode.value = ''

    if (response.price_sync_status === 'failed') {
      actionMessage.value = `${response.stock_code} was added, but the latest price sync failed. The item is marked as failed until a future sync succeeds.`
    } else if (response.price_sync_status === 'pending') {
      actionMessage.value = `${response.stock_code} was added to the watchlist. Latest price sync is queued; refresh or run Sync to see the updated status.`
    } else {
      actionMessage.value = `${response.stock_code} was added to the watchlist.`
    }

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
  singleSyncErrors.value = { ...singleSyncErrors.value, [stockCode]: '' }

  try {
    const response = await stockStore.syncSinglePrice(stockCode)
    actionMessage.value = response?.message || `${stockCode} synced successfully.`
    await stockStore.fetchFilterResults()
  } catch (error) {
    const message = error.message || `Unable to sync ${stockCode}.`
    singleSyncErrors.value = { ...singleSyncErrors.value, [stockCode]: message }
  }
}

async function handleSyncAll() {
  actionMessage.value = ''
  actionError.value = ''

  try {
    const response = await stockStore.syncAllPrices()
    const failedCodes = response.failed_codes?.length ? ` Failed: ${response.failed_codes.join(', ')}.` : ''
    actionMessage.value = `${response.message}${failedCodes}`
    await stockStore.fetchFilterResults()
  } catch (error) {
    actionError.value = error.message || 'Unable to sync watchlist prices.'
  }
}

async function handleSyncFundamentals() {
  actionMessage.value = ''
  actionError.value = ''

  try {
    await stockStore.syncFundamentals()
    actionMessage.value = 'Fundamentals synced for watchlist items.'
  } catch (error) {
    actionError.value = error.message || 'Unable to sync fundamentals.'
  }
}

onMounted(refreshStocksView)
</script>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.table-wrap {
  overflow-x: auto;
}

.helper-text {
  margin: 6px 0;
  color: #66788a;
  font-size: 14px;
}

.status-detail {
  margin-top: 6px;
  color: #66788a;
  font-size: 12px;
  line-height: 1.5;
}

.row-action-btn {
  margin-left: 8px;
}

.error-inline {
  color: #9a2c2c;
}

.stocks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.result-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 12px;
}

.result-item {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 12px;
}

.muted {
  color: #66788a;
  font-size: 12px;
  line-height: 1.4;
}

.result-pass {
  background: #edf8f2;
  border: 1px solid #cae9d5;
}

.result-fail {
  background: #fdf0ef;
  border: 1px solid #f4d0cd;
}
</style>
