<template>
  <section class="card trade-summary-card">
    <div class="section-header">
      <div>
        <h2>{{ t('stocks.trades.summaryTitle') }}</h2>
        <p class="helper-text">{{ t('stocks.trades.summarySubtitle') }}</p>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="!items.length" class="empty-state">{{ t('stocks.trades.summaryEmpty') }}</div>
    <div v-else class="trade-summary-grid">
      <article v-for="item in items" :key="item.currency" class="trade-summary-panel">
        <div class="tile-head">
          <strong>{{ item.currency }}</strong>
          <span class="badge" :class="item.realized_pnl >= 0 ? 'badge-success' : 'badge-danger'">
            {{ formatSignedCurrency(item.realized_pnl, item.currency) }}
          </span>
        </div>
        <div class="trade-summary-stats">
          <article v-for="stat in buildStats(item)" :key="`${item.currency}-${stat.label}`" class="portfolio-summary-item">
            <span class="fundamentals-label">{{ stat.label }}</span>
            <strong>{{ stat.value }}</strong>
          </article>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatCurrency as formatCurrencyValue } from '@/utils/formatters'

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({ items: [] })
  },
  error: {
    type: String,
    default: ''
  }
})

const { t, locale } = useI18n()

const items = computed(() => Array.isArray(props.summary?.items) ? props.summary.items : [])

function formatPrice(value, currency) {
  return formatCurrencyValue(Number(value || 0), locale.value, currency || null)
}

function formatSignedCurrency(value, currency) {
  const amount = Number(value || 0)
  return `${amount > 0 ? '+' : ''}${formatPrice(amount, currency)}`
}

function buildStats(item) {
  return [
    { label: t('stocks.trades.summary.buyCount'), value: String(item.buy_count || 0) },
    { label: t('stocks.trades.summary.sellCount'), value: String(item.sell_count || 0) },
    { label: t('stocks.trades.summary.openingBalanceCount'), value: String(item.opening_balance_count || 0) },
    { label: t('stocks.trades.summary.openingBalanceShares'), value: String(item.opening_balance_shares || 0) },
    { label: t('stocks.trades.summary.boughtShares'), value: String(item.bought_shares || 0) },
    { label: t('stocks.trades.summary.soldShares'), value: String(item.sold_shares || 0) },
    { label: t('stocks.trades.summary.grossProceeds'), value: formatPrice(item.gross_proceeds, item.currency) },
    { label: t('stocks.trades.summary.matchedCostBasis'), value: formatPrice(item.matched_cost_basis, item.currency) },
    { label: t('stocks.trades.summary.fees'), value: formatPrice(item.fees, item.currency) },
    { label: t('stocks.trades.summary.taxes'), value: formatPrice(item.taxes, item.currency) }
  ]
}
</script>

<style scoped>
.trade-summary-card,
.trade-summary-panel,
.trade-summary-stats {
  display: grid;
  gap: 12px;
}

.trade-summary-grid,
.trade-summary-stats {
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.trade-summary-panel {
  padding: 14px;
  border: 1px solid #e1eaf2;
  border-radius: 14px;
  background: #fbfdff;
}
</style>
