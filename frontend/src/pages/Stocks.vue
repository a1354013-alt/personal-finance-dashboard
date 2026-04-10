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
        <button class="btn btn-secondary" :disabled="stockStore.syncLoading" @click="handleSyncAll">
          {{ stockStore.syncLoading ? 'Syncing...' : 'Sync Prices' }}
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
                  {{ statusLabel(item.price_sync_status, item.price) }}
                </span>
              </td>
              <td>
                <button class="btn btn-danger" @click="handleDeleteWatchlist(item.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card">
      <h2>Screening Coverage</h2>
      <p class="helper-text">
        {{ stockStore.filterMetadata?.message || 'Screening metadata unavailable.' }}
      </p>
      <p class="helper-text" v-if="stockStore.filterMetadata">
        Supported mock codes: {{ stockStore.filterMetadata.supported_codes.join(', ') }}
      </p>
    </section>

    <div class="stocks-grid">
      <section class="card">
        <h2>Passed</h2>
        <div v-if="stockStore.filterLoading" class="loading-text">Loading screening results...</div>
        <div v-else-if="stockStore.filterError" class="error-msg">{{ stockStore.filterError }}</div>
        <div v-else-if="stockStore.passedStocks.length === 0" class="empty-state">No watchlist items passed the mock screen.</div>
        <ul v-else class="result-list">
          <li v-for="stock in stockStore.passedStocks" :key="stock.stock_code" class="result-item result-pass">
            <strong>{{ stock.stock_code }}</strong>
            <span>Passed all mock rules.</span>
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

function formatPrice(value) {
  return `NT$ ${Number(value).toLocaleString('zh-TW', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function statusLabel(status, price) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'failed'
  if (!price) return 'pending'
  return 'pending'
}

function statusBadgeClass(status) {
  if (status === 'success') return 'badge-success'
  if (status === 'failed') return 'badge-danger'
  return 'badge-warning'
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

.result-pass {
  background: #edf8f2;
  border: 1px solid #cae9d5;
}

.result-fail {
  background: #fdf0ef;
  border: 1px solid #f4d0cd;
}
</style>
