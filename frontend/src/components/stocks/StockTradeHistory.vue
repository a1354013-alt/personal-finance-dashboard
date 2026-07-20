<template>
  <section class="card trade-history-card">
    <div class="section-header">
      <div>
        <h2>{{ t('stocks.trades.historyTitle') }}</h2>
        <p class="helper-text">{{ t('stocks.trades.historySubtitle') }}</p>
      </div>
    </div>

    <div class="form-row trade-filter-row">
      <div class="form-group">
        <label for="trade-filter-stock-code">{{ t('stocks.trades.stockCode') }}</label>
        <input id="trade-filter-stock-code" v-model.trim="draftFilters.stock_code" type="text" placeholder="AAPL" />
      </div>
      <div class="form-group">
        <label for="trade-filter-type">{{ t('stocks.trades.tradeType') }}</label>
        <select id="trade-filter-type" v-model="draftFilters.trade_type">
          <option value="">{{ t('common.all') }}</option>
          <option value="OPENING_BALANCE">{{ t('stocks.trades.types.OPENING_BALANCE') }}</option>
          <option value="BUY">{{ t('stocks.trades.types.BUY') }}</option>
          <option value="SELL">{{ t('stocks.trades.types.SELL') }}</option>
        </select>
      </div>
      <div class="form-group">
        <label for="trade-filter-date-from">{{ t('stocks.trades.dateFrom') }}</label>
        <input id="trade-filter-date-from" v-model="draftFilters.date_from" type="date" />
      </div>
      <div class="form-group">
        <label for="trade-filter-date-to">{{ t('stocks.trades.dateTo') }}</label>
        <input id="trade-filter-date-to" v-model="draftFilters.date_to" type="date" />
      </div>
      <div class="holding-form-actions">
        <button type="button" class="btn btn-primary" @click="applyFilters">{{ t('stocks.trades.applyFilters') }}</button>
        <button type="button" class="btn btn-secondary" @click="$emit('refresh')">{{ t('common.refresh') }}</button>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="loading" class="loading-text">{{ t('stocks.trades.loading') }}</div>
    <div v-else-if="!trades.length" class="empty-state">{{ t('stocks.trades.empty') }}</div>
    <div v-else class="trade-history-list">
      <article v-for="trade in trades" :key="trade.id" class="watchlist-tile">
        <div class="tile-head">
          <div>
            <strong>{{ trade.stock_code }}</strong>
            <div class="tile-name">{{ t(`stocks.trades.types.${trade.trade_type}`) }}</div>
          </div>
          <span class="badge" :class="trade.trade_type === 'SELL' ? 'badge-danger' : 'badge-success'">
            {{ trade.trade_date }}
          </span>
        </div>
        <div class="portfolio-metrics-grid">
          <article class="portfolio-metric-item">
            <span>{{ t('stocks.trades.shares') }}</span>
            <strong>{{ trade.shares }}</strong>
          </article>
          <article class="portfolio-metric-item">
            <span>{{ t('stocks.trades.price') }}</span>
            <strong>{{ formatPrice(trade.price, trade.currency) }}</strong>
          </article>
          <article class="portfolio-metric-item">
            <span>{{ t('stocks.trades.fee') }}</span>
            <strong>{{ formatPrice(trade.fee, trade.currency) }}</strong>
          </article>
          <article class="portfolio-metric-item">
            <span>{{ t('stocks.trades.tax') }}</span>
            <strong>{{ formatPrice(trade.tax, trade.currency) }}</strong>
          </article>
        </div>
        <div v-if="trade.note" class="tile-meta">{{ trade.note }}</div>
        <div class="tile-actions">
          <button class="btn btn-secondary" @click="$emit('edit', trade)">{{ t('common.edit') }}</button>
          <button class="btn btn-danger" :disabled="isDeleting(trade.id)" @click="$emit('delete', trade)">{{ t('common.delete') }}</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
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

const emit = defineEmits(['apply:filters', 'refresh', 'edit', 'delete'])
const { t, locale } = useI18n()
const draftFilters = ref({ ...props.filters })

watch(
  () => props.filters,
  (value) => {
    draftFilters.value = { ...value }
  },
  { deep: true }
)

function applyFilters() {
  emit('apply:filters', { ...draftFilters.value })
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
