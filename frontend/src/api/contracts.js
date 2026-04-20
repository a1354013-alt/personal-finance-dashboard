/**
 * Centralized API contract normalizers for stable UI state shapes.
 * This project is intentionally JS-first; these helpers reduce implicit fields and magic strings.
 */

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
 * @property {number} user_id
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
    id: Number(row.id),
    user_id: Number(row.user_id),
    stock_code: String(row.stock_code || '').toUpperCase(),
    name: String(row.name || row.stock_code || '').trim(),
    price: row.price == null ? null : Number(row.price),
    date: row.date || null,
    volume: row.volume == null ? null : Number(row.volume),
    price_sync_status: status,
    last_sync_error: row.last_sync_error || null,
    last_sync_attempt_at: row.last_sync_attempt_at || null,
    price_sync: priceSync
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
    ttl_hours: Number(row.ttl_hours ?? 0),
    timeout_seconds: Number(row.timeout_seconds ?? 0),
    message: String(row.message || '')
  }
}

/**
 * @param {any} row
 * @returns {any}
 */
export function normalizeFundamentalsFilterResult(row) {
  if (!row || typeof row !== 'object') return null
  return {
    stock_code: String(row.stock_code || '').toUpperCase(),
    passed: Boolean(row.passed),
    fail_reasons: Array.isArray(row.fail_reasons) ? row.fail_reasons : [],
    fundamentals: row.fundamentals ?? null,
    meta: row.meta ?? null
  }
}

