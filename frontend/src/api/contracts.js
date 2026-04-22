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
    note: toStringOrEmpty(row.note),
    created_at: row.created_at || null
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
    category: toStringOrEmpty(row.category),
    monthly_limit: toNumberOrZero(row.monthly_limit),
    current_spent: toNumberOrZero(row.current_spent),
    percent_used: toNumberOrZero(row.percent_used),
    over_budget: Boolean(row.over_budget),
    created_at: row.created_at || null
  }
}

/**
 * @param {any} payload
 * @returns {any|null}
 */
export function normalizeDashboardSummary(payload) {
  if (!payload || typeof payload !== 'object') return null

  return {
    total_income: toNumberOrZero(payload.total_income),
    total_expense: toNumberOrZero(payload.total_expense),
    net_balance: toNumberOrZero(payload.net_balance),
    expense_by_category: Array.isArray(payload.expense_by_category) ? payload.expense_by_category : [],
    monthly_trend: Array.isArray(payload.monthly_trend) ? payload.monthly_trend : [],
    over_budget: Array.isArray(payload.over_budget) ? payload.over_budget : [],
    summary_scope: payload.summary_scope ?? { totals: 'all_time', over_budget: 'current_month' }
  }
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

