import { describe, expect, it } from 'vitest'

import en from './en'
import zhTW from './zh-TW'
import zhCN from './zh-CN'
import ja from './ja'

function flattenKeys(value, prefix = '') {
  return Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key
    if (child && typeof child === 'object' && !Array.isArray(child)) {
      return flattenKeys(child, path)
    }
    return [path]
  })
}

function flattenMessages(value, prefix = '') {
  return Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key
    if (child && typeof child === 'object' && !Array.isArray(child)) {
      return flattenMessages(child, path)
    }
    return [[path, child]]
  })
}

function suspiciousCodePoint(value) {
  for (const char of value) {
    const codePoint = char.codePointAt(0)
    if (
      codePoint === 0xfffd ||
      (codePoint >= 0x80 && codePoint <= 0x9f) ||
      (codePoint >= 0xe000 && codePoint <= 0xf8ff)
    ) {
      return `U+${codePoint.toString(16).toUpperCase().padStart(4, '0')}`
    }
  }
  return null
}

describe('locale message key parity', () => {
  const locales = {
    en,
    'zh-TW': zhTW,
    'zh-CN': zhCN,
    ja
  }
  const expectedKeys = flattenKeys(en).sort()

  it.each(Object.entries(locales).filter(([locale]) => locale !== 'en'))('%s matches the English message keys', (_locale, messages) => {
    expect(flattenKeys(messages).sort()).toEqual(expectedKeys)
  })

  it.each(Object.entries(locales))('%s has no mojibake sentinel code points', (locale, messages) => {
    for (const [key, value] of flattenMessages(messages)) {
      if (typeof value !== 'string') {
        continue
      }
      const codePoint = suspiciousCodePoint(value)
      expect(codePoint, `${locale}.${key} contains suspicious code point ${codePoint}`).toBeNull()
    }
  })

  it('localizes the Holdings-managed trade marker', () => {
    expect(en.stocks.trades.managedThroughHoldings).toBe('Managed through Holdings')
    expect(zhTW.stocks.trades.managedThroughHoldings).toBe('透過持股管理')
    expect(zhCN.stocks.trades.managedThroughHoldings).toBe('通过持仓管理')
    expect(ja.stocks.trades.managedThroughHoldings).toBe('保有銘柄で管理')
  })
})
