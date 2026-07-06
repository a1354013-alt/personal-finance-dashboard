/**
 * Centralized API contract normalizers for stable UI state shapes.
 * This project is intentionally JS-first; these helpers reduce implicit fields and magic strings.
 */

function toNumberOrNull(value) {
  if (value == null) return null
  const num = Number(value)
  return Number.isFinite(num) ? num : null
}

function toNumberOrZero(value) {
  const num = Number(value ?? 0)
  return Number.isFinite(num) ? num : 0
}

function toStringOrEmpty(value) {
  return value == null ? '' : String(value)
}

function toTrimmedStringOrEmpty(value) {
  return toStringOrEmpty(value).trim()
}

export function normalizeEmail(email) {
  return toStringOrEmpty(email).trim().toLowerCase()
}

/**
 * @param {any} user
 * @returns {{id:number, email:string}|null}
 */
export function normalizeUser(user) {
  if (!user || typeof user !== 'object') return null
  const id = Number(user.id)
  if (!Number.isFinite(id)) return null
  return {
    id,
    email: normalizeEmail(user.email)
  }
}

/**
 * @typedef {'pending'|'success'|'failed'|'ready'|'sync_required'|'sync_queued'|'unsupported'|'error'} SyncStatus
 */

/**
 * @typedef {Object} PriceSyncMeta
 * @property {SyncStatus} status
 * @property {string} provider
 * @property {string|null} [as_of_date]
 * @property {string|null} [last_attempt_at]
 * @property {string|null} [error_message]
 */

/**
 * @typedef {Object} WatchlistItem
 * @property {number} id
 * @property {string} stock_code
 * @property {string} name
 * @property {string|null} currency
 * @property {number|null} price
 * @property {string|null} date
 * @property {number|null} volume
 * @property {SyncStatus} price_sync_status
 * @property {string|null} last_sync_error
 * @property {string|null} last_sync_attempt_at
 * @property {PriceSyncMeta|null} price_sync
 */

/**
 * @param {any} row
 * @returns {WatchlistItem|null}
 */
export function normalizeWatchlistItem(row) {
  if (!row || typeof row !== 'object') return null

  const id = toNumberOrNull(row.id)
  if (id == null) return null

  const status = row.price_sync_status === 'success' || row.price_sync_status === 'failed' ? row.price_sync_status : 'pending'
  const syncStatus = ['ready', 'sync_required', 'sync_queued', 'unsupported', 'error'].includes(row.sync_status)
    ? row.sync_status
    : status === 'success'
      ? 'ready'
      : status === 'failed'
        ? 'error'
        : 'sync_required'
  const priceSync = row.price_sync && typeof row.price_sync === 'object'
    ? {
        status: row.price_sync.status || status,
        provider: String(row.price_sync.provider || 'unknown'),
        as_of_date: row.price_sync.as_of_date || row.date || null,
        last_attempt_at: row.price_sync.last_attempt_at || row.last_sync_attempt_at || null,
        error_message: row.price_sync.error_message || row.last_sync_error || null
      }
    : null

  return {
    id,
    stock_code: String(row.stock_code || '').toUpperCase(),
    symbol: String(row.symbol || row.stock_code || '').toUpperCase(),
    name: String(row.name || row.stock_code || '').trim(),
    currency: row.currency == null ? null : String(row.currency).trim().toUpperCase(),
    market: row.market == null ? null : String(row.market).trim(),
    exchange: row.exchange == null ? null : String(row.exchange).trim(),
    price: toNumberOrNull(row.price ?? row.last_price),
    last_price: toNumberOrNull(row.last_price ?? row.price),
    previous_close: toNumberOrNull(row.previous_close),
    price_change: toNumberOrNull(row.price_change),
    change_percent: toNumberOrNull(row.change_percent),
    date: row.date || null,
    volume: toNumberOrNull(row.volume),
    provider: row.provider == null ? null : String(row.provider).trim(),
    price_updated_at: row.price_updated_at || null,
    sync_status: syncStatus,
    sync_required: Boolean(row.sync_required ?? syncStatus !== 'ready'),
    sync_error: row.sync_error || row.last_sync_error || null,
    ai_summary: toTrimmedStringOrEmpty(row.ai_summary),
    ai_risk_notes: toTrimmedStringOrEmpty(row.ai_risk_notes),
    ai_updated_at: row.ai_updated_at || null,
    price_sync_status: status,
    last_sync_error: row.last_sync_error || null,
    last_sync_attempt_at: row.last_sync_attempt_at || null,
    price_sync: priceSync
  }
}

/**
 * @param {any} row
 * @returns {any|null}
 */
export function normalizeExpense(row) {
  if (!row || typeof row !== 'object') return null
  const id = toNumberOrNull(row.id)
  if (id == null) return null
  return {
    id,
    amount: toNumberOrZero(row.amount),
    category: toStringOrEmpty(row.category),
    type: row.type === 'income' ? 'income' : 'expense',
    date: row.date || null,
    note: toStringOrEmpty(row.note)
  }
}

/**
 * @param {any} row
 * @returns {any|null}
 */
export function normalizeBudget(row) {
  if (!row || typeof row !== 'object') return null
  const id = toNumberOrNull(row.id)
  if (id == null) return null
  return {
    id,
    month: toStringOrEmpty(row.month),
    category: toStringOrEmpty(row.category),
    amount: toNumberOrZero(row.amount),
    current_spent: toNumberOrZero(row.current_spent),
    percent_used: toNumberOrZero(row.percent_used)
  }
}

/**
 * @param {any} payload
 * @returns {any|null}
 */
export function normalizeBudgetSummary(payload) {
  if (!payload || typeof payload !== 'object') return null
  return {
    month: toStringOrEmpty(payload.month),
    totalBudget: toNumberOrZero(payload.totalBudget ?? payload.total_budget),
    totalUsed: toNumberOrZero(payload.totalUsed ?? payload.total_used),
    totalRemaining: toNumberOrZero(payload.totalRemaining ?? payload.total_remaining),
    items: Array.isArray(payload.items)
      ? payload.items.map(item => ({
        id: toNumberOrNull(item.id),
        category: toStringOrEmpty(item.category),
        budget: toNumberOrZero(item.budget),
        used: toNumberOrZero(item.used ?? item.currentSpent ?? item.current_spent),
        remaining: toNumberOrZero(item.remaining),
        usageRate: toNumberOrZero(item.usageRate ?? item.usagePercent ?? item.percent_used),
        status: toStringOrEmpty(item.status),
        over_budget: Boolean(item.over_budget ?? item.overBudget),
        warning: Boolean(item.warning)
      }))
      : []
  }
}

/**
 * @param {any} payload
 * @returns {any|null}
 */
export function normalizeDashboardSummary(payload) {
  if (!payload || typeof payload !== 'object') return null

  return {
    monthlyIncome: toNumberOrZero(payload.monthlyIncome ?? payload.monthly_income),
    monthlyExpense: toNumberOrZero(payload.monthlyExpense ?? payload.monthly_expense),
    monthlyBalance: toNumberOrZero(payload.monthlyBalance ?? payload.monthly_balance),
    topExpenseCategory: payload.topExpenseCategory || payload.top_expense_category
      ? String(payload.topExpenseCategory ?? payload.top_expense_category)
      : null,
    monthlyTrend: Array.isArray(payload.monthlyTrend ?? payload.monthly_trend)
      ? (payload.monthlyTrend ?? payload.monthly_trend).map(item => ({
        month: String(item.month || ''),
        income: toNumberOrZero(item.income),
        expense: toNumberOrZero(item.expense)
      }))
      : [],
    expenseByCategory: Array.isArray(payload.expenseByCategory ?? payload.expense_by_category)
      ? (payload.expenseByCategory ?? payload.expense_by_category).map(item => ({
        category: String(item.category || ''),
        amount: toNumberOrZero(item.amount)
      }))
      : [],
    recentTransactions: Array.isArray(payload.recentTransactions ?? payload.recent_transactions)
      ? (payload.recentTransactions ?? payload.recent_transactions).map(item => ({
        date: String(item.date || ''),
        category: String(item.category || ''),
        type: String(item.type || ''),
        amount: toNumberOrZero(item.amount)
      }))
      : [],
    totalBudget: toNumberOrZero(payload.totalBudget ?? payload.total_budget),
    totalUsed: toNumberOrZero(payload.totalUsed ?? payload.total_used),
    totalRemaining: toNumberOrZero(payload.totalRemaining ?? payload.total_remaining),
    budgetOverCount: toNumberOrZero(payload.budgetOverCount ?? payload.budget_over_count),
    budgetWarningCount: toNumberOrZero(payload.budgetWarningCount ?? payload.budget_warning_count),
    budgetItems: Array.isArray(payload.budgetItems ?? payload.budget_items)
      ? (payload.budgetItems ?? payload.budget_items).map(item => ({
        category: String(item.category || ''),
        amount: toNumberOrZero(item.amount ?? item.budget),
        used: toNumberOrZero(item.used ?? item.currentSpent ?? item.current_spent),
        remaining: toNumberOrZero(item.remaining),
        usagePercent: toNumberOrZero(item.usagePercent ?? item.usageRate ?? item.usage_percent ?? item.percent_used),
        status: String(item.status || 'safe'),
        overBudget: Boolean(item.overBudget ?? item.over_budget),
        warning: Boolean(item.warning)
      }))
      : []
  }
}

export function normalizeDashboardCharts(payload) {
  if (!payload || typeof payload !== 'object') return null
  return {
    monthly_expense_trend: Array.isArray(payload.monthly_expense_trend ?? payload.monthlyExpenseTrend)
      ? (payload.monthly_expense_trend ?? payload.monthlyExpenseTrend)
      : [],
    category_distribution: Array.isArray(payload.category_distribution ?? payload.categoryDistribution)
      ? (payload.category_distribution ?? payload.categoryDistribution)
      : [],
    net_income_trend: Array.isArray(payload.net_income_trend ?? payload.netIncomeTrend)
      ? (payload.net_income_trend ?? payload.netIncomeTrend)
      : [],
    budget_usage: Array.isArray(payload.budget_usage ?? payload.budgetUsage)
      ? (payload.budget_usage ?? payload.budgetUsage).map(item => ({
        category: String(item.category || ''),
        amount: toNumberOrZero(item.amount),
        currentSpent: toNumberOrZero(item.currentSpent ?? item.current_spent),
        usagePercent: toNumberOrZero(item.usagePercent ?? item.percent_used ?? item.usage_rate),
        status: String(item.status || 'safe'),
        overBudget: Boolean(item.overBudget ?? item.over_budget),
        warning: Boolean(item.warning)
      }))
      : []
  }
}

/**
 * @param {any} payload
 * @returns {string}
 */
export function normalizeAiSummary(payload) {
  if (!payload || typeof payload !== 'object') return ''
  return toTrimmedStringOrEmpty(payload.summary)
}

/**
 * @param {any} payload
 * @returns {string}
 */
export function normalizeBudgetAdvice(payload) {
  if (!payload || typeof payload !== 'object') return ''
  return toTrimmedStringOrEmpty(payload.advice)
}

/**
 * @param {any} row
 * @returns {any}
 */
export function normalizeFilterMetadata(row) {
  if (!row || typeof row !== 'object') return null
  return {
    fundamentals_provider: String(row.fundamentals_provider || ''),
    ttl_hours: toNumberOrZero(row.ttl_hours),
    timeout_seconds: toNumberOrZero(row.timeout_seconds),
    message: String(row.message || '')
  }
}

/**
 * @param {any} row
 * @returns {any|null}
 */
export function normalizeFundamentalsSnapshot(row) {
  if (!row || typeof row !== 'object') return null
  return {
    stock_code: String(row.stock_code || '').toUpperCase(),
    source: row.source == null ? null : String(row.source),
    provider: row.source == null ? null : String(row.source),
    as_of_date: row.as_of_date || null,
    fetched_at: row.fetched_at || null,
    status: row.status == null ? null : String(row.status),
    error_message: row.error_message || null,
    pe_ratio: toNumberOrNull(row.pe_ratio),
    pb_ratio: toNumberOrNull(row.pb_ratio),
    dividend_yield: toNumberOrNull(row.dividend_yield),
    revenue_growth: toNumberOrNull(row.revenue_growth),
    eps: toNumberOrNull(row.eps)
  }
}

/**
 * @param {any} row
 * @returns {any|null}
 */
export function normalizeFundamentalsMeta(row) {
  if (!row || typeof row !== 'object') return null
  return {
    provider: String(row.provider || ''),
    ttl_hours: toNumberOrZero(row.ttl_hours),
    is_stale: Boolean(row.is_stale),
    fetched_at: row.fetched_at || null,
    as_of_date: row.as_of_date || null,
    status: row.status == null ? null : String(row.status),
    error_message: row.error_message || null
  }
}

/**
 * @param {any} row
 * @returns {any|null}
 */
export function normalizeFundamentalsFilterResult(row) {
  if (!row || typeof row !== 'object') return null
  return {
    stock_code: String(row.stock_code || '').toUpperCase(),
    passed: Boolean(row.passed),
    fail_reasons: Array.isArray(row.fail_reasons) ? row.fail_reasons : [],
    fundamentals: normalizeFundamentalsSnapshot(row.fundamentals),
    meta: normalizeFundamentalsMeta(row.meta)
  }
}

export function normalizePriceHistoryPoint(row) {
  if (!row || typeof row !== 'object') return null
  return {
    trade_date: row.trade_date || null,
    close: toNumberOrNull(row.close),
    open: toNumberOrNull(row.open),
    high: toNumberOrNull(row.high),
    low: toNumberOrNull(row.low),
    volume: toNumberOrNull(row.volume)
  }
}

export function normalizeStockAiExplanation(payload) {
  if (!payload) return null
  if (typeof payload === 'string') {
    const explanation = toTrimmedStringOrEmpty(payload)
    return explanation
      ? {
          status: 'ready',
          stock_code: '',
          message: '',
          explanation,
          can_sync: false,
          job_id: null,
          request_id: null,
          meta: null
        }
      : null
  }
  if (typeof payload !== 'object') return null

  const status = ['ready', 'sync_required', 'sync_queued', 'unsupported'].includes(payload.status)
    ? payload.status
    : 'sync_required'

  return {
    status,
    stock_code: String(payload.stock_code || '').toUpperCase(),
    message: toTrimmedStringOrEmpty(payload.message),
    explanation: toTrimmedStringOrEmpty(payload.explanation),
    can_sync: Boolean(payload.can_sync),
    job_id: toNumberOrNull(payload.job_id),
    request_id: toTrimmedStringOrEmpty(payload.request_id),
    meta: payload.meta && typeof payload.meta === 'object'
      ? {
          provider: toTrimmedStringOrEmpty(payload.meta.provider),
          is_fallback: Boolean(payload.meta.is_fallback),
          error: toTrimmedStringOrEmpty(payload.meta.error)
        }
      : null
  }
}

export function normalizeStockAiAnalysis(payload) {
  if (!payload || typeof payload !== 'object') return null
  const status = ['ready', 'sync_required', 'unsupported', 'error'].includes(payload.status)
    ? payload.status
    : 'error'
  return {
    status,
    stock_code: String(payload.stock_code || '').toUpperCase(),
    summary: toTrimmedStringOrEmpty(payload.summary),
    recent_price_movement: toTrimmedStringOrEmpty(payload.recent_price_movement),
    volume_note: toTrimmedStringOrEmpty(payload.volume_note),
    risk_notes: Array.isArray(payload.risk_notes) ? payload.risk_notes.map(toStringOrEmpty).filter(Boolean) : [],
    watch_points: Array.isArray(payload.watch_points) ? payload.watch_points.map(toStringOrEmpty).filter(Boolean) : [],
    disclaimer: toTrimmedStringOrEmpty(payload.disclaimer),
    meta: payload.meta && typeof payload.meta === 'object'
      ? {
          provider: toTrimmedStringOrEmpty(payload.meta.provider),
          is_fallback: Boolean(payload.meta.is_fallback),
          error: toTrimmedStringOrEmpty(payload.meta.error)
        }
      : null
  }
}

export function normalizeStockDashboard(payload) {
  if (!payload || typeof payload !== 'object') return null
  return {
    selected_stock_code: payload.selected_stock_code || null,
    watchlist: Array.isArray(payload.watchlist) ? payload.watchlist.map(normalizeWatchlistItem).filter(Boolean) : [],
    price_history: Array.isArray(payload.price_history) ? payload.price_history.map(normalizePriceHistoryPoint).filter(Boolean) : [],
    fundamentals: payload.fundamentals ? normalizeFundamentalsSnapshot(payload.fundamentals) : null,
    ai_explanation: normalizeStockAiExplanation(payload.ai_explanation)
  }
}

