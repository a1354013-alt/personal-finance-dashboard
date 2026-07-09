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

describe('locale message key parity', () => {
  const locales = {
    'zh-TW': zhTW,
    'zh-CN': zhCN,
    ja
  }
  const expectedKeys = flattenKeys(en).sort()

  it.each(Object.entries(locales))('%s matches the English message keys', (_locale, messages) => {
    expect(flattenKeys(messages).sort()).toEqual(expectedKeys)
  })
})
