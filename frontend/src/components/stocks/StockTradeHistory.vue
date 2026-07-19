<template>
  <section class="card trade-history-card">
    <div class="section-header">
      <div>
        <h2>Trade History</h2>
        <p class="helper-text">Newest first, with filters for symbol, type, and trade date range.</p>
      </div>
    </div>

    <div class="form-row trade-filter-row">
      <div class="form-group">
        <label for="trade-filter-stock-code">Stock Code</label>
        <input
          id="trade-filter-stock-code"
          :value="filters.stock_code"
          type="text"
          placeholder="AAPL"
          @input="emitFilter('stock_code', $event.target.value)"
        />
      </div>
      <div class="form-group">
        <label for="trade-filter-type">Trade Type</label>
        <select id="trade-filter-type" :value="filters.trade_type" @change="emitFilter('trade_type', $event.target.value)">
          <option value="">All</option>
          <option value="OPENING_BALANCE">OPENING_BALANCE</option>
          <option value="BUY">BUY</option>
          <option value="SELL">SELL</option>
        </select>
      </div>
      <div class="form-group">
        <label for="trade-filter-date-from">Date From</label>
        <input id="trade-filter-date-from" :value="filters.date_from" type="date" @input="emitFilter('date_from', $event.target.value)" />
      </div>
      <div class="form-group">
        <label for="trade-filter-date-to">Date To</label>
        <input id="trade-filter-date-to" :value="filters.date_to" type="date" @input="emitFilter('date_to', $event.target.value)" />
      </div>
      <div class="holding-form-actions">
        <button type="button" class="btn btn-secondary" @click="$emit('refresh')">Refresh</button>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="loading" class="loading-text">Loading trades…</div>
    <div v-else-if="!trades.length" class="empty-state">No trades match the current filters.</div>
    <div v-else class="trade-history-list">
      <article v-for="trade in trades" :key="trade.id" class="watchlist-tile">
        <div class="tile-head">
          <div>
            <strong>{{ trade.stock_code }}</strong>
            <div class="tile-name">{{ trade.trade_type }}</div>
          </div>
          <span class="badge" :class="trade.trade_type === 'SELL' ? 'badge-danger' : 'badge-success'">
            {{ trade.trade_date }}
          </span>
        </div>
        <div class="portfolio-metrics-grid">
          <article class="portfolio-metric-item">
            <span>Shares</span>
            <strong>{{ trade.shares }}</strong>
          </article>
          <article class="portfolio-metric-item">
            <span>Price</span>
            <strong>{{ formatPrice(trade.price, trade.currency) }}</strong>
          </article>
          <article class="portfolio-metric-item">
            <span>Fee</span>
            <strong>{{ formatPrice(trade.fee, trade.currency) }}</strong>
          </article>
          <article class="portfolio-metric-item">
            <span>Tax</span>
            <strong>{{ formatPrice(trade.tax, trade.currency) }}</strong>
          </article>
        </div>
        <div v-if="trade.note" class="tile-meta">{{ trade.note }}</div>
        <div class="tile-actions">
          <button class="btn btn-secondary" @click="$emit('edit', trade)">Edit</button>
          <button class="btn btn-danger" :disabled="isDeleting(trade.id)" @click="$emit('delete', trade)">Delete</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { formatCurrency as formatCurrencyValue } from '@/utils/formatters'

const props = defineProps({
  trades: {
    type: Array,
    default: () => []
  },
  filters: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  deletingIds: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:filters', 'refresh', 'edit', 'delete'])
const { locale } = useI18n()

function emitFilter(name, value) {
  emit('update:filters', { ...props.filters, [name]: value })
}

function isDeleting(id) {
  return props.deletingIds.includes(Number(id))
}

function formatPrice(value, currency) {
  return formatCurrencyValue(Number(value || 0), locale.value, currency || null)
}
</script>

<style scoped>
.trade-history-card,
.trade-filter-row,
.trade-history-list {
  display: grid;
  gap: 16px;
}

.trade-history-list {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
</style>
