import { createI18n } from 'vue-i18n'
import en from './messages/en'
import zhTW from './messages/zh-TW'

export const DEFAULT_LOCALE = 'zh-TW'
export const SUPPORTED_LOCALES = ['zh-TW', 'en']
const LOCALE_KEY = 'locale'

function getInitialLocale() {
  if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
    return DEFAULT_LOCALE
  }

  try {
    const saved = localStorage.getItem(LOCALE_KEY)
    return SUPPORTED_LOCALES.includes(saved) ? saved : DEFAULT_LOCALE
  } catch {
    return DEFAULT_LOCALE
  }
}

export function createI18nInstance() {
  return createI18n({
    legacy: false,
    locale: getInitialLocale(),
    fallbackLocale: 'en',
    globalInjection: true,
    messages: {
      'zh-TW': zhTW,
      en
    }
  })
}

export function persistLocale(locale) {
  if (typeof window === 'undefined' || typeof localStorage === 'undefined') return
  try {
    localStorage.setItem(LOCALE_KEY, locale)
  } catch {
    // ignore storage failures
  }
}

const i18n = createI18nInstance()

export default i18n
