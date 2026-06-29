export function formatCurrency(value, locale = 'zh-TW', currency = 'TWD') {
  const amount = Number(value)
  if (!Number.isFinite(amount)) {
    return '--'
  }

  const currencyMap = {
    TWD: 'NT$',
    USD: 'US$'
  }

  const normalizedCurrency = currency == null ? '' : String(currency).trim().toUpperCase()
  const prefix = normalizedCurrency ? (currencyMap[normalizedCurrency] || normalizedCurrency) : ''
  const formatted = amount.toLocaleString(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  })

  return prefix ? `${prefix} ${formatted}` : formatted
}

export function formatPercent(value, locale = 'zh-TW', digits = 1) {
  return `${Number(value || 0).toLocaleString(locale, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  })}%`
}

export function formatCompactPercent(value) {
  return `${Math.round(Number(value || 0))}%`
}
