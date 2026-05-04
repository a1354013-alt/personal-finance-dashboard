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
 * @typedef {'pending'|'success'|'failed'} SyncStatus
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
    name: String(row.name || row.stock_code || '').trim(),
    price: toNumberOrNull(row.price),
    date: row.date || null,
    volume: toNumberOrNull(row.volume),
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
    amount: toNumberOrZero(row.amount || row.monthly_limit),
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
    totalBudget: toNumberOrZero(payload.totalBudget),
    totalUsed: toNumberOrZero(payload.totalUsed),
    totalRemaining: toNumberOrZero(payload.totalRemaining),
    items: Array.isArray(payload.items)
      ? payload.items.map(item => ({
        id: toNumberOrNull(item.id),
        category: toStringOrEmpty(item.category),
        budget: toNumberOrZero(item.budget),
        used: toNumberOrZero(item.used),
        remaining: toNumberOrZero(item.remaining),
        usageRate: toNumberOrZero(item.usageRate),
        status: toStringOrEmpty(item.status)
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
    monthlyIncome: toNumberOrZero(payload.monthlyIncome),
    monthlyExpense: toNumberOrZero(payload.monthlyExpense),
    monthlyBalance: toNumberOrZero(payload.monthlyBalance),
    topExpenseCategory: payload.topExpenseCategory ? String(payload.topExpenseCategory) : null,
    monthlyTrend: Array.isArray(payload.monthlyTrend)
      ? payload.monthlyTrend.map(item => ({
        month: String(item.month || ''),
        income: toNumberOrZero(item.income),
        expense: toNumberOrZero(item.expense)
      }))
      : [],
    expenseByCategory: Array.isArray(payload.expenseByCategory)
      ? payload.expenseByCategory.map(item => ({
        category: String(item.category || ''),
        amount: toNumberOrZero(item.amount)
      }))
      : [],
    recentTransactions: Array.isArray(payload.recentTransactions)
      ? payload.recentTransactions.map(item => ({
        date: String(item.date || ''),
        category: String(item.category || ''),
        type: String(item.type || ''),
        amount: toNumberOrZero(item.amount)
      }))
      : [],
    totalBudget: toNumberOrZero(payload.totalBudget),
    totalUsed: toNumberOrZero(payload.totalUsed),
    totalRemaining: toNumberOrZero(payload.totalRemaining),
    budgetOverCount: toNumberOrZero(payload.budgetOverCount),
    budgetWarningCount: toNumberOrZero(payload.budgetWarningCount),
    budgetItems: Array.isArray(payload.budgetItems)
      ? payload.budgetItems.map(item => ({
        category: String(item.category || ''),
        budget: toNumberOrZero(item.budget),
        used: toNumberOrZero(item.used),
        remaining: toNumberOrZero(item.remaining),
        usageRate: toNumberOrZero(item.usageRate),
        status: String(item.status || 'safe')
      }))
      : []
  }
}

export function normalizeDashboardCharts(payload) {
  if (!payload || typeof payload !== 'object') return null
  return {
    monthly_expense_trend: Array.isArray(payload.monthly_expense_trend) ? payload.monthly_expense_trend : [],
    category_distribution: Array.isArray(payload.category_distribution) ? payload.category_distribution : [],
    net_income_trend: Array.isArray(payload.net_income_trend) ? payload.net_income_trend : [],
    budget_usage: Array.isArray(payload.budget_usage) ? payload.budget_usage : []
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

export function normalizeStockDashboard(payload) {
  if (!payload || typeof payload !== 'object') return null
  return {
    selected_stock_code: payload.selected_stock_code || null,
    watchlist: Array.isArray(payload.watchlist) ? payload.watchlist.map(normalizeWatchlistItem).filter(Boolean) : [],
    price_history: Array.isArray(payload.price_history) ? payload.price_history.map(normalizePriceHistoryPoint).filter(Boolean) : [],
    fundamentals: payload.fundamentals ? normalizeFundamentalsSnapshot(payload.fundamentals) : null,
    ai_explanation: toTrimmedStringOrEmpty(payload.ai_explanation)
  }
}

