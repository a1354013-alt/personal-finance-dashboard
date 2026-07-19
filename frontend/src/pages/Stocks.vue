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

    <section class="card portfolio-card">
      <div class="section-header">
        <div>
          <h2>{{ t('stocks.portfolio.title') }}</h2>
          <p class="helper-text">{{ t('stocks.portfolio.subtitle') }}</p>
        </div>
        <span class="badge" :class="portfolioPnLClass">{{ portfolioPnLLabel }}</span>
      </div>

      <div v-if="stockStore.holdingsError" class="error-msg">{{ stockStore.holdingsError }}</div>

      <div v-if="portfolioCurrencySections.length" class="portfolio-currency-sections">
        <article v-for="section in portfolioCurrencySections" :key="section.currency" class="portfolio-currency-section">
          <div class="tile-head">
            <strong>{{ section.currency }}</strong>
            <span class="badge" :class="section.badgeClass">{{ section.badgeLabel }}</span>
          </div>
          <div class="portfolio-summary-grid">
            <article v-for="item in section.items" :key="`${section.currency}-${item.label}`" class="portfolio-summary-item">
              <span class="fundamentals-label">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </article>
          </div>
        </article>
      </div>

      <div v-if="portfolioWarnings.length" class="portfolio-warning-list">
        <div v-for="warning in portfolioWarnings" :key="warning" class="tile-warning">{{ warning }}</div>
      </div>

      <form class="form-row holding-form" @submit.prevent="handleSaveHolding">
        <div class="form-group">
          <label for="holding-stock-code">{{ t('stocks.portfolio.stockCode') }}</label>
          <input id="holding-stock-code" v-model.trim="holdingForm.stock_code" type="text" placeholder="2330 or AAPL" required />
        </div>
        <div class="form-group">
          <label for="holding-shares">{{ t('stocks.portfolio.shares') }}</label>
          <input id="holding-shares" v-model.number="holdingForm.shares" type="number" min="0.000001" step="0.000001" required />
        </div>
        <div class="form-group">
          <label for="holding-average-cost">{{ t('stocks.portfolio.averageCost') }}</label>
          <input id="holding-average-cost" v-model.number="holdingForm.average_cost" type="number" min="0.0001" step="0.0001" required />
        </div>
        <div class="form-group">
          <label for="holding-note">{{ t('stocks.portfolio.note') }}</label>
          <input id="holding-note" v-model.trim="holdingForm.note" type="text" :placeholder="t('stocks.portfolio.notePlaceholder')" />
        </div>
        <div class="holding-form-actions">
          <button type="submit" class="btn btn-primary" :disabled="stockStore.holdingsSaving">
            {{ stockStore.holdingsSaving ? t('stocks.portfolio.saving') : editingHoldingId ? t('stocks.portfolio.update') : t('stocks.portfolio.create') }}
          </button>
          <button v-if="editingHoldingId" type="button" class="btn btn-secondary" @click="resetHoldingForm">
            {{ t('stocks.portfolio.cancelEdit') }}
          </button>
        </div>
      </form>

      <div v-if="stockStore.holdingsLoading || stockStore.portfolioLoading" class="loading-text">{{ t('stocks.portfolio.loading') }}</div>
      <div v-else-if="!stockStore.holdings.length" class="empty-state">{{ t('stocks.portfolio.empty') }}</div>
      <div v-else class="portfolio-position-list">
        <article v-for="position in portfolioPositions" :key="position.holding_id" class="portfolio-position-card">
          <div class="tile-head">
            <div>
              <strong>{{ position.stock_code }}</strong>
              <div class="tile-name">{{ position.stock_name || position.stock_code }}</div>
            </div>
            <span class="badge" :class="position.unrealized_pnl == null ? 'badge-warning' : position.unrealized_pnl >= 0 ? 'badge-success' : 'badge-danger'">
              {{ allocationBadgeText(position) }}
            </span>
          </div>
          <div class="portfolio-metrics-grid">
            <article v-for="metric in buildPositionMetrics(position)" :key="metric.label" class="portfolio-metric-item">
              <span>{{ metric.label }}</span>
              <strong :class="metric.tone">{{ metric.value }}</strong>
            </article>
          </div>
          <div v-if="position.warning" class="tile-warning">{{ position.warning }}</div>
          <div v-if="holdingNote(position.holding_id)" class="tile-meta">{{ holdingNote(position.holding_id) }}</div>
          <div class="tile-actions">
            <button class="btn btn-secondary" @click="startEditingHolding(position.holding_id)">{{ t('common.edit') }}</button>
            <button class="btn btn-danger" :disabled="stockStore.isHoldingDeleting(position.holding_id)" @click="handleDeleteHolding(position.holding_id)">
              {{ t('common.delete') }}
            </button>
          </div>
        </article>
      </div>
    </section>

    <RealizedPnlSummary
      :summary="stockStore.tradeSummary"
      :error="stockStore.tradesError"
    />

    <StockTradeForm
      :model-value="tradeForm"
      :saving="stockStore.tradesSaving"
      :error="stockStore.tradesError || actionError"
      :editing-trade-id="editingTradeId"
      @submit="handleSaveTrade"
      @cancel="resetTradeForm"
    />

    <StockTradeHistory
      :trades="stockStore.trades"
      :filters="tradeFilters"
      :loading="stockStore.tradesLoading"
      :error="stockStore.tradesError"
      :deleting-ids="stockStore.tradesDeletingIds"
      @update:filters="handleTradeFilterChange"
      @refresh="refreshTradeWorkspace"
      @edit="startEditingTrade"
      @delete="handleDeleteTrade"
    />

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

        <section class="card indicators-card">
          <div class="section-header">
            <h2>{{ t('stocks.indicators.title') }}</h2>
            <span v-if="stockStore.selectedIndicators" class="badge" :class="indicatorBadgeClass(stockStore.selectedIndicators.status)">
              {{ indicatorStatusText(stockStore.selectedIndicators.status) }}
            </span>
          </div>
          <div v-if="stockStore.indicatorsError" class="error-msg">{{ stockStore.indicatorsError }}</div>
          <div v-else-if="stockStore.selectedWatchlistItem && stockStore.isIndicatorLoading(stockStore.selectedWatchlistItem.id)" class="loading-text">
            {{ t('stocks.indicators.loading') }}
          </div>
          <div v-else-if="!stockStore.selectedIndicators" class="empty-state">{{ t('stocks.indicators.empty') }}</div>
          <template v-else>
            <div v-if="stockStore.selectedIndicators.status !== 'ready'" class="tile-warning">
              {{ indicatorStatusText(stockStore.selectedIndicators.status) }}
            </div>
            <div class="indicator-grid">
              <article v-for="item in indicatorItems" :key="item.label" class="indicator-item">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </article>
            </div>
            <small class="disclaimer-text">{{ stockStore.selectedIndicators.disclaimer }}</small>
          </template>
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
            <div class="tile-price">{{ item.price != null ? formatPrice(item.price, item.currency) : t('stocks.noDataPrice') }}</div>
            <div class="tile-meta">{{ item.market || item.exchange ? [item.market, item.exchange].filter(Boolean).join(' / ') : item.provider }}</div>
            <div class="tile-meta">{{ item.date || t('stocks.awaitingPriceHistory') }}</div>
            <div v-if="item.change_percent != null" class="tile-change" :class="{ positive: item.change_percent > 0, negative: item.change_percent < 0 }">
              {{ formatChange(item.price_change, item.change_percent) }}
            </div>
            <div v-if="item.sync_status === 'sync_required'" class="tile-warning">{{ t('stocks.syncRequired') }}</div>
            <div v-if="item.sync_status === 'unsupported'" class="tile-warning">{{ t('stocks.ai.unsupported') }}</div>
            <div class="tile-actions">
              <button class="btn btn-primary" :disabled="stockStore.isItemSyncing(item.id)" @click="handleSyncWatchlistItem(item)">
                {{ stockStore.isItemSyncing(item.id) ? t('stocks.queueing') : t('stocks.queuePriceSync') }}
              </button>
              <button class="btn btn-secondary" :disabled="stockStore.isAnalyzing(item.id)" @click="handleAnalyzeWatchlistItem(item)">
                {{ stockStore.isAnalyzing(item.id) ? t('stocks.ai.analyzing') : t('stocks.ai.runInterpretation') }}
              </button>
              <button class="btn btn-danger" :disabled="stockStore.deleting" @click="handleDeleteWatchlist(item.id)">{{ t('common.delete') }}</button>
            </div>
            <div v-if="item.sync_error || item.last_sync_error" class="tile-error">{{ item.sync_error || item.last_sync_error }}</div>
            <div v-if="stockStore.aiAnalysisById[item.id]" class="stock-ai-analysis">
              <strong>{{ t('stocks.ai.interpretation') }}</strong>
              <p>{{ stockStore.aiAnalysisById[item.id].summary }}</p>
              <p v-if="stockStore.aiAnalysisById[item.id].recent_price_movement">{{ stockStore.aiAnalysisById[item.id].recent_price_movement }}</p>
              <p v-if="stockStore.aiAnalysisById[item.id].volume_note">{{ stockStore.aiAnalysisById[item.id].volume_note }}</p>
              <ul v-if="stockStore.aiAnalysisById[item.id].risk_notes.length">
                <li v-for="note in stockStore.aiAnalysisById[item.id].risk_notes" :key="note">{{ note }}</li>
              </ul>
              <small>{{ stockStore.aiAnalysisById[item.id].disclaimer }}</small>
            </div>
          </article>
        </div>
      </section>

      <section class="card alerts-card">
        <div class="section-header">
          <h2>{{ t('stocks.alerts.title') }}</h2>
          <button class="btn btn-secondary" :disabled="stockStore.alertsChecking" @click="handleCheckAlerts">
            {{ stockStore.alertsChecking ? t('stocks.alerts.checking') : t('stocks.alerts.check') }}
          </button>
        </div>
        <form v-if="stockStore.selectedWatchlistItem" class="form-row alert-form" @submit.prevent="handleCreateAlert">
          <div class="form-group">
            <label for="alert-condition">{{ t('stocks.alerts.condition') }}</label>
            <select id="alert-condition" v-model="newAlert.condition_type">
              <option value="above">{{ t('stocks.alerts.above') }}</option>
              <option value="below">{{ t('stocks.alerts.below') }}</option>
            </select>
          </div>
          <div class="form-group">
            <label for="alert-price">{{ t('stocks.alerts.targetPrice') }}</label>
            <input id="alert-price" v-model.number="newAlert.target_price" type="number" min="0.01" step="0.01" required />
          </div>
          <button type="submit" class="btn btn-primary" :disabled="isCreatingAlert">
            {{ isCreatingAlert ? t('stocks.alerts.creating') : t('stocks.alerts.create') }}
          </button>
        </form>
        <div v-if="stockStore.alertsError" class="error-msg">{{ stockStore.alertsError }}</div>
        <div v-else-if="stockStore.alertsLoading" class="loading-text">{{ t('stocks.alerts.loading') }}</div>
        <div v-else-if="stockStore.alerts.length === 0" class="empty-state">{{ t('stocks.alerts.empty') }}</div>
        <ul v-else class="alert-list">
          <li v-for="alert in stockStore.alerts" :key="alert.id" class="alert-row">
            <div>
              <strong>{{ alert.symbol }}</strong>
              <span>{{ alertConditionText(alert) }}</span>
            </div>
            <span class="badge" :class="alert.triggered_at ? 'badge-danger' : alert.is_active ? 'badge-success' : 'badge-warning'">
              {{ alert.triggered_at ? t('stocks.alerts.triggered') : alert.is_active ? t('stocks.alerts.active') : t('stocks.alerts.inactive') }}
            </span>
            <div class="alert-actions">
              <button class="btn btn-secondary" :disabled="Boolean(alert.triggered_at)" @click="handleToggleAlert(alert)">
                {{ alert.is_active ? t('stocks.alerts.deactivate') : t('stocks.alerts.activate') }}
              </button>
              <button class="btn btn-danger" @click="handleDeleteAlert(alert.id)">{{ t('common.delete') }}</button>
            </div>
            <small v-if="alert.triggered_at">
              {{ t('stocks.alerts.triggeredAt', { price: formatPrice(alert.last_price_at_trigger, alertCurrency(alert)) }) }}
            </small>
          </li>
        </ul>
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
import RealizedPnlSummary from '@/components/stocks/RealizedPnlSummary.vue'
import StockTradeForm from '@/components/stocks/StockTradeForm.vue'
import StockTradeHistory from '@/components/stocks/StockTradeHistory.vue'
import { useStockStore } from '@/stores/stockStore'
import { formatCurrency as formatCurrencyValue } from '@/utils/formatters'

const stockStore = useStockStore()
const newStockCode = ref('')
const isAdding = ref(false)
const isCreatingAlert = ref(false)
const newAlert = ref({ condition_type: 'above', target_price: null })
const editingHoldingId = ref(null)
const editingTradeId = ref(null)
const holdingForm = ref({ stock_code: '', shares: null, average_cost: null, note: '' })
const tradeForm = ref({
  stock_code: '',
  trade_type: 'BUY',
  trade_date: '2026-07-19',
  shares: null,
  price: null,
  fee: 0,
  tax: 0,
  note: ''
})
const tradeFilters = ref({ stock_code: '', trade_type: '', date_from: '', date_to: '' })
const actionMessage = ref('')
const actionError = ref('')
const { t, locale } = useI18n()

function formatPrice(value, currency) {
  return formatCurrencyValue(Number(value), locale.value, currency || null)
}

function formatSignedCurrency(value, currency) {
  const amount = Number(value || 0)
  const sign = amount > 0 ? '+' : ''
  return `${sign}${formatPrice(amount, currency)}`
}

function formatChange(priceChange, changePercent) {
  const change = Number(priceChange || 0)
  const percent = Number(changePercent || 0)
  const sign = change > 0 ? '+' : ''
  return `${sign}${change.toFixed(2)} (${sign}${percent.toFixed(2)}%)`
}

function statusBadgeClass(status) {
  if (status === 'success') return 'badge-success'
  if (status === 'failed') return 'badge-danger'
  return 'badge-warning'
}

function indicatorBadgeClass(status) {
  if (status === 'ready') return 'badge-success'
  if (status === 'insufficient_history') return 'badge-warning'
  return 'badge-danger'
}

function indicatorStatusText(status) {
  if (status === 'ready') return t('stocks.indicators.ready')
  if (status === 'insufficient_history') return t('stocks.indicators.insufficient')
  return t('stocks.indicators.noHistory')
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
const selectedCurrency = computed(() => stockStore.selectedWatchlistItem?.currency || null)
const portfolioCurrencyTotals = computed(() => stockStore.portfolio?.currency_totals || [])
const portfolioWarnings = computed(() => stockStore.portfolio?.warnings || [])
const portfolioPositions = computed(() => stockStore.portfolio?.positions || [])

function buildCurrencySummaryItems(total) {
  const items = [
    {
      label: total.is_partial ? t('stocks.portfolio.pricedMarketValue') : t('stocks.portfolio.totalMarketValue'),
      value: total.total_market_value == null ? t('common.empty') : formatPrice(total.total_market_value, total.currency)
    },
    {
      label: t('stocks.portfolio.totalCost'),
      value: formatPrice(total.total_cost || 0, total.currency)
    },
    {
      label: t('stocks.portfolio.totalPnL'),
      value: total.total_unrealized_pnl == null ? t('common.empty') : formatSignedCurrency(total.total_unrealized_pnl, total.currency)
    },
    {
      label: t('stocks.portfolio.pricedHoldings'),
      value: `${total.priced_holdings_count || 0}/${total.holdings_count || 0}`
    },
    {
      label: t('stocks.portfolio.holdingsCount'),
      value: String(total.holdings_count || 0)
    }
  ]
  if (total.is_partial) {
    items.push(
      {
        label: t('stocks.portfolio.missingPriceCount'),
        value: String(total.missing_price_count || 0)
      },
      {
        label: t('stocks.portfolio.unpricedCost'),
        value: formatPrice(total.unpriced_cost || 0, total.currency)
      }
    )
  }
  return items
}

const portfolioCurrencySections = computed(() => portfolioCurrencyTotals.value.map((total) => {
  const percent = total.total_unrealized_pnl_percent
  return {
    currency: total.currency,
    badgeClass: total.total_unrealized_pnl == null ? 'badge-warning' : total.total_unrealized_pnl >= 0 ? 'badge-success' : 'badge-danger',
    badgeLabel: total.is_partial
      ? t('stocks.portfolio.partialSummary')
      : percent == null ? t('stocks.portfolio.pricePending') : t('stocks.portfolio.pnlPercent', { value: percent.toFixed(2) }),
    items: buildCurrencySummaryItems(total)
  }
}))

const portfolioPnLClass = computed(() => {
  if (portfolioCurrencyTotals.value.length !== 1) return 'badge-warning'
  const pnl = portfolioCurrencyTotals.value[0]?.total_unrealized_pnl
  if (pnl == null) return 'badge-warning'
  return pnl >= 0 ? 'badge-success' : 'badge-danger'
})

const portfolioPnLLabel = computed(() => {
  if (portfolioCurrencyTotals.value.length > 1) return t('stocks.portfolio.mixedCurrencies')
  if (portfolioCurrencyTotals.value[0]?.is_partial) return t('stocks.portfolio.partialSummary')
  const percent = portfolioCurrencyTotals.value[0]?.total_unrealized_pnl_percent
  if (percent == null) return t('stocks.portfolio.pricePending')
  return t('stocks.portfolio.pnlPercent', { value: percent.toFixed(2) })
})

const indicatorItems = computed(() => {
  const indicators = stockStore.selectedIndicators
  if (!indicators) return []
  return [
    { label: 'MA5', value: indicators.ma5 == null ? t('common.empty') : formatPrice(indicators.ma5, selectedCurrency.value) },
    { label: 'MA20', value: indicators.ma20 == null ? t('common.empty') : formatPrice(indicators.ma20, selectedCurrency.value) },
    { label: 'RSI14', value: indicators.rsi14 == null ? t('common.empty') : indicators.rsi14.toFixed(2) },
    { label: t('stocks.indicators.latestClose'), value: indicators.latest_close == null ? t('common.empty') : formatPrice(indicators.latest_close, selectedCurrency.value) }
  ]
})

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
    { label: 'Source', value: fundamentals.source || t('common.empty') },
    { label: 'Status', value: fundamentals.status || t('common.empty') }
  ]
})

async function refreshStockWorkspace(selectedCode = null) {
  await Promise.allSettled([
    stockStore.refreshPortfolioWorkspace(),
    stockStore.refreshTradeWorkspace(tradeFilters.value),
    stockStore.fetchDashboard(selectedCode),
    stockStore.fetchFilterResults(),
    stockStore.listStockAlerts()
  ])
}

async function refreshTradeWorkspace() {
  await stockStore.refreshTradeWorkspace(tradeFilters.value)
}

function resetHoldingForm() {
  editingHoldingId.value = null
  holdingForm.value = { stock_code: '', shares: null, average_cost: null, note: '' }
}

function resetTradeForm() {
  editingTradeId.value = null
  tradeForm.value = {
    stock_code: '',
    trade_type: 'BUY',
    trade_date: '2026-07-19',
    shares: null,
    price: null,
    fee: 0,
    tax: 0,
    note: ''
  }
}

function holdingById(holdingId) {
  return stockStore.holdings.find((item) => item.id === Number(holdingId)) || null
}

function holdingNote(holdingId) {
  return holdingById(holdingId)?.note || ''
}

function startEditingHolding(holdingId) {
  const holding = holdingById(holdingId)
  if (!holding) return
  editingHoldingId.value = holding.id
  holdingForm.value = {
    stock_code: holding.stock_code,
    shares: holding.shares,
    average_cost: holding.average_cost,
    note: holding.note || ''
  }
}

function startEditingTrade(trade) {
  editingTradeId.value = trade.id
  tradeForm.value = {
    stock_code: trade.stock_code,
    trade_type: trade.trade_type === 'OPENING_BALANCE' ? 'BUY' : trade.trade_type,
    trade_date: trade.trade_date,
    shares: trade.shares,
    price: trade.price,
    fee: trade.fee,
    tax: trade.tax,
    note: trade.note || ''
  }
}

function buildPositionMetrics(position) {
  return [
    {
      label: t('stocks.portfolio.shares'),
      value: position.shares == null ? t('common.empty') : String(position.shares),
      tone: ''
    },
    {
      label: t('stocks.portfolio.averageCost'),
      value: position.average_cost == null ? t('common.empty') : formatPrice(position.average_cost, position.currency),
      tone: ''
    },
    {
      label: t('stocks.portfolio.latestPrice'),
      value: position.latest_price == null ? t('common.empty') : formatPrice(position.latest_price, position.currency),
      tone: ''
    },
    {
      label: t('stocks.portfolio.marketValue'),
      value: position.market_value == null ? t('common.empty') : formatPrice(position.market_value, position.currency),
      tone: ''
    },
    {
      label: t('stocks.portfolio.costBasis'),
      value: position.cost_basis == null ? t('common.empty') : formatPrice(position.cost_basis, position.currency),
      tone: ''
    },
    {
      label: t('stocks.portfolio.unrealizedPnL'),
      value: position.unrealized_pnl == null
        ? t('common.empty')
        : `${formatSignedCurrency(position.unrealized_pnl, position.currency)} (${position.unrealized_pnl_percent?.toFixed(2) ?? '0.00'}%)`,
      tone: position.unrealized_pnl == null ? '' : position.unrealized_pnl >= 0 ? 'positive' : 'negative'
    }
  ]
}

function allocationBadgeText(position) {
  if (position.allocation_percent != null) {
    return t('stocks.portfolio.allocationValue', {
      currency: position.currency,
      value: position.allocation_percent.toFixed(2)
    })
  }
  if (position.market_value == null) {
    return t('stocks.portfolio.pricePending')
  }
  return t('common.empty')
}

async function handleSaveHolding() {
  if (!holdingForm.value.stock_code || !holdingForm.value.shares || !holdingForm.value.average_cost) return
  actionMessage.value = ''
  actionError.value = ''
  try {
    if (editingHoldingId.value) {
      await stockStore.updateHolding(editingHoldingId.value, holdingForm.value)
      actionMessage.value = t('stocks.portfolio.updated')
    } else {
      await stockStore.createHolding(holdingForm.value)
      actionMessage.value = t('stocks.portfolio.created')
    }
    resetHoldingForm()
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleDeleteHolding(holdingId) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.deleteHolding(holdingId)
    if (editingHoldingId.value === Number(holdingId)) {
      resetHoldingForm()
    }
    actionMessage.value = t('stocks.portfolio.deleted')
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleSaveTrade(payload) {
  if (!payload.stock_code || !payload.trade_date || !payload.shares || payload.price == null) return
  actionMessage.value = ''
  actionError.value = ''
  try {
    if (editingTradeId.value) {
      await stockStore.updateTrade(editingTradeId.value, payload, tradeFilters.value)
      actionMessage.value = 'Trade updated.'
    } else {
      await stockStore.createTrade(payload, tradeFilters.value)
      actionMessage.value = 'Trade created.'
    }
    resetTradeForm()
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleDeleteTrade(trade) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.deleteTrade(trade.id, tradeFilters.value)
    if (editingTradeId.value === Number(trade.id)) {
      resetTradeForm()
    }
    actionMessage.value = 'Trade deleted.'
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleTradeFilterChange(nextFilters) {
  tradeFilters.value = nextFilters
  await refreshTradeWorkspace()
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

async function handleSyncWatchlistItem(item) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    const response = await stockStore.syncWatchlistItem(item.id)
    actionMessage.value = response?.sync_status === 'ready'
      ? `${response.stock_code} ${t('stocks.syncComplete')}`
      : response?.sync_error || `${item.stock_code} ${t('stocks.syncQueued')}`
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleAnalyzeWatchlistItem(item) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    const response = await stockStore.analyzeWatchlistItem(item.id)
    if (response?.status === 'sync_required') {
      actionError.value = response.summary || t('stocks.syncRequired')
      return
    }
    actionMessage.value = t('stocks.ai.interpretationReady')
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

async function handleCreateAlert() {
  if (!stockStore.selectedWatchlistItem) return
  actionMessage.value = ''
  actionError.value = ''
  isCreatingAlert.value = true
  try {
    await stockStore.createStockAlert(stockStore.selectedWatchlistItem.id, {
      condition_type: newAlert.value.condition_type,
      target_price: Number(newAlert.value.target_price)
    })
    newAlert.value = { condition_type: 'above', target_price: null }
    actionMessage.value = t('stocks.alerts.created')
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  } finally {
    isCreatingAlert.value = false
  }
}

async function handleToggleAlert(alert) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.updateStockAlert(alert.id, { is_active: !alert.is_active })
    actionMessage.value = alert.is_active ? t('stocks.alerts.deactivated') : t('stocks.alerts.activated')
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleDeleteAlert(alertId) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.deleteStockAlert(alertId)
    actionMessage.value = t('common.delete')
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

async function handleCheckAlerts() {
  actionMessage.value = ''
  actionError.value = ''
  try {
    const result = await stockStore.checkStockAlerts()
    actionMessage.value = t('stocks.alerts.checked', { count: result?.triggered_count || 0 })
  } catch (error) {
    actionError.value = error.message || t('common.unknownError')
  }
}

function alertConditionText(alert) {
  const condition = alert.condition_type === 'below' ? t('stocks.alerts.below') : t('stocks.alerts.above')
  return `${condition} ${formatPrice(alert.target_price, alertCurrency(alert))}`
}

function alertCurrency(alert) {
  const item = stockStore.watchlist.find((candidate) => (
    candidate.id === alert.watchlist_item_id ||
    candidate.stock_code === alert.symbol ||
    candidate.symbol === alert.symbol
  ))
  return item?.currency || selectedCurrency.value
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

.watchlist-grid,
.portfolio-position-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.watchlist-tile,
.portfolio-position-card {
  border: 1px solid #e1eaf2;
  border-radius: 16px;
  padding: 16px;
  background: linear-gradient(180deg, #fff 0%, #f7fbfd 100%);
}

.portfolio-card {
  display: grid;
  gap: 16px;
}

.portfolio-currency-sections {
  display: grid;
  gap: 12px;
}

.portfolio-currency-section {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid #e1eaf2;
  border-radius: 8px;
  background: #fbfdff;
}

.portfolio-summary-grid,
.portfolio-metrics-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.portfolio-summary-item,
.portfolio-metric-item {
  padding: 14px;
  border-radius: 14px;
  background: #f5f8fb;
  display: grid;
  gap: 8px;
}

.portfolio-warning-list {
  display: grid;
  gap: 8px;
}

.holding-form {
  align-items: end;
}

.holding-form-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tile-name,
.tile-meta,
.helper-text,
.fundamentals-label,
.portfolio-metric-item span {
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

.tile-warning {
  margin-top: 8px;
  color: #7c5200;
  font-size: 12px;
  font-weight: 700;
}

.tile-change {
  margin-top: 8px;
  font-weight: 700;
  color: #445767;
}

.tile-change.positive,
.positive {
  color: #12733d;
}

.tile-change.negative,
.negative {
  color: #a33a2b;
}

.stock-ai-analysis {
  display: grid;
  gap: 8px;
  margin-top: 14px;
  padding: 12px;
  border-radius: 8px;
  background: #f5f8fb;
  border: 1px solid #e1eaf2;
}

.stock-ai-analysis p,
.stock-ai-analysis ul {
  margin: 0;
}

.stock-ai-analysis ul {
  padding-left: 18px;
}

.fundamentals-card,
.indicators-card,
.ai-card {
  min-height: 340px;
}

.fundamentals-grid,
.indicator-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.fundamentals-item,
.indicator-item {
  padding: 14px;
  border-radius: 14px;
  background: #f5f8fb;
  display: grid;
  gap: 8px;
}

.indicator-item {
  min-height: 82px;
}

.disclaimer-text,
.alert-row small {
  color: #66788a;
}

.alert-form {
  align-items: end;
  margin: 14px 0;
}

.alert-list,
.result-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}

.alert-row {
  display: grid;
  grid-template-columns: minmax(160px, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e1eaf2;
  border-radius: 8px;
  background: #f7fafc;
}

.alert-row > div:first-child,
.result-list li {
  display: grid;
  gap: 4px;
}

.result-list li {
  padding: 14px;
  border-radius: 14px;
  background: #f7fafc;
}

.alert-actions,
.ai-status-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
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

@media (max-width: 760px) {
  .alert-row {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .alert-actions,
  .ai-status-actions {
    justify-content: flex-start;
  }
}
</style>
