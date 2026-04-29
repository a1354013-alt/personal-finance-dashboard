export function formatCurrency(value, locale = 'zh-TW') {
  return `NT$ ${Number(value || 0).toLocaleString(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  })}`
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
