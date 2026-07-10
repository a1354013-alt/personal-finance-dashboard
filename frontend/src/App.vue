<template>
  <div id="app-wrapper">
    <header v-if="authStore.isAuthenticated" class="app-shell-header">
      <nav class="navbar">
        <div class="navbar-brand">
          <div class="brand-mark" aria-hidden="true">
            <span />
            <span />
          </div>
          <div>
            <strong>{{ t('common.appTitle') }}</strong>
            <p>v{{ VERSION }}</p>
          </div>
        </div>

        <ul class="navbar-links">
          <li v-for="item in navItems" :key="item.to">
            <router-link :to="item.to" exact-active-class="active" active-class="active">
              {{ item.label }}
            </router-link>
          </li>
        </ul>

        <div class="navbar-actions">
          <div class="locale-switcher" role="group" :aria-label="t('common.language')">
            <button
              v-for="option in localeOptions"
              :key="option.value"
              type="button"
              class="locale-btn"
              :class="{ active: locale === option.value }"
              @click="setLocale(option.value)"
            >
              {{ option.label }}
            </button>
          </div>

          <span v-if="authStore.user" class="user-email">{{ authStore.user.email }}</span>
          <button class="btn btn-ghost" @click="handleLogout">{{ t('nav.logout') }}</button>
        </div>
      </nav>
    </header>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { VERSION } from '@/constants/version'
import { persistLocale } from '@/i18n'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
const router = useRouter()
const { t, locale } = useI18n()

const navItems = computed(() => [
  { to: '/', label: t('nav.dashboard') },
  { to: '/expenses', label: t('nav.expenses') },
  { to: '/recurring-transactions', label: t('nav.recurring') },
  { to: '/imports/transactions', label: t('nav.imports') },
  { to: '/budgets', label: t('nav.budgets') },
  { to: '/stocks', label: t('nav.stocks') }
])

const localeOptions = computed(() => [
  { value: 'zh-TW', label: '繁中' },
  { value: 'zh-CN', label: '简中' },
  { value: 'en', label: 'EN' },
  { value: 'ja', label: '日本語' }
])

onMounted(async () => {
  if (authStore.token && !authStore.user) {
    const success = await authStore.fetchMe()
    if (!success) {
      router.push('/login')
    }
  }
})

function setLocale(nextLocale) {
  locale.value = nextLocale
  persistLocale(nextLocale)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style>
:root {
  font-family: 'Segoe UI', 'Noto Sans TC', sans-serif;
  color: #233441;
  background: #f5f4ef;
  color-scheme: light;
  --bg-soft: #f7f4ee;
  --bg-mist: #edf3ef;
  --bg-blue: #edf3f6;
  --surface: rgba(255, 255, 255, 0.82);
  --surface-strong: rgba(255, 255, 255, 0.94);
  --surface-dark: rgba(22, 40, 52, 0.72);
  --text-main: #233441;
  --text-muted: #627484;
  --border-soft: rgba(129, 151, 166, 0.18);
  --shadow-soft: 0 18px 46px rgba(51, 72, 84, 0.08);
  --radius-lg: 24px;
  --radius-md: 18px;
}

* {
  box-sizing: border-box;
}

html {
  background:
    radial-gradient(circle at top left, rgba(227, 214, 182, 0.58), transparent 28%),
    radial-gradient(circle at top right, rgba(194, 219, 209, 0.52), transparent 24%),
    linear-gradient(180deg, #faf8f2 0%, #eef3f5 56%, #edf4ef 100%);
}

body {
  margin: 0;
  min-width: 320px;
  color: var(--text-main);
  background: transparent;
}

button,
input,
select,
textarea {
  font: inherit;
}

a {
  color: inherit;
}

#app-wrapper {
  min-height: 100vh;
}

.app-shell-header {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: 18px 18px 0;
}

.navbar {
  max-width: 1240px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 20px;
  padding: 14px 18px;
  border: 1px solid rgba(222, 231, 236, 0.42);
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(18, 35, 46, 0.82), rgba(28, 53, 68, 0.66));
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 42px rgba(28, 46, 58, 0.12);
  color: #f8fbfd;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.navbar-brand strong {
  display: block;
  font-size: 15px;
  letter-spacing: 0.02em;
}

.navbar-brand p {
  margin: 3px 0 0;
  color: rgba(225, 234, 238, 0.72);
  font-size: 12px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(245, 250, 246, 0.18), rgba(140, 200, 175, 0.24));
  display: grid;
  place-items: center;
  grid-template-columns: repeat(2, 8px);
  gap: 6px;
  box-shadow: inset 0 0 0 1px rgba(240, 248, 252, 0.14);
}

.brand-mark span {
  display: block;
  width: 8px;
  border-radius: 999px;
  background: #d8eee4;
}

.brand-mark span:first-child {
  height: 18px;
}

.brand-mark span:last-child {
  height: 26px;
  background: #f4d9b8;
}

.navbar-links {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.navbar-links a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  text-decoration: none;
  color: rgba(235, 243, 247, 0.8);
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.navbar-links a.active,
.navbar-links a:hover {
  color: #0f2230;
  background: rgba(244, 248, 249, 0.92);
  transform: translateY(-1px);
}

.navbar-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.locale-switcher {
  display: inline-flex;
  align-items: center;
  padding: 4px;
  border-radius: 999px;
  background: rgba(245, 250, 252, 0.12);
  border: 1px solid rgba(230, 239, 244, 0.14);
}

.locale-btn {
  min-width: 72px;
  min-height: 34px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(236, 244, 247, 0.74);
  cursor: pointer;
}

.locale-btn.active {
  background: rgba(255, 255, 255, 0.92);
  color: #143041;
  font-weight: 700;
}

.user-email {
  font-size: 13px;
  color: rgba(231, 239, 243, 0.82);
}

.main-content {
  max-width: 1240px;
  margin: 0 auto;
  padding: 26px 18px 48px;
}

.page-header {
  margin-bottom: 22px;
}

.page-header h1 {
  margin: 0 0 8px;
  font-size: 32px;
  line-height: 1.15;
}

.page-header p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.card {
  background: var(--surface-strong);
  border-radius: var(--radius-lg);
  padding: 22px;
  box-shadow: var(--shadow-soft);
  border: 1px solid var(--border-soft);
}

.card h2 {
  margin: 0;
  font-size: 19px;
  color: var(--text-main);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 8px 16px;
  border: 0;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.18s ease, opacity 0.18s ease, box-shadow 0.18s ease;
}

.btn:hover {
  opacity: 0.96;
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.58;
  cursor: not-allowed;
  transform: none;
}

.btn-primary {
  background: linear-gradient(135deg, #214e68 0%, #2e7e76 100%);
  color: #fff;
  box-shadow: 0 10px 24px rgba(47, 122, 118, 0.2);
}

.btn-secondary {
  background: #eaf0f4;
  color: #28404f;
}

.btn-success {
  background: #1f8f5f;
  color: #fff;
}

.btn-danger {
  background: #d16158;
  color: #fff;
}

.btn-ghost {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 180px;
  flex: 1;
}

.form-group label {
  font-size: 13px;
  color: #526576;
  font-weight: 700;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid rgba(181, 196, 207, 0.58);
  border-radius: 16px;
  font-size: 14px;
  color: #223441;
  background: rgba(255, 255, 255, 0.88);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: rgba(53, 118, 124, 0.52);
  box-shadow: 0 0 0 4px rgba(72, 143, 146, 0.14);
  background: #fff;
}

.error-msg,
.success-msg {
  border-radius: 16px;
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.6;
}

.error-msg {
  color: #94453d;
  background: rgba(255, 243, 239, 0.95);
  border: 1px solid rgba(233, 193, 180, 0.92);
}

.success-msg {
  color: #225f4a;
  background: rgba(236, 248, 241, 0.98);
  border: 1px solid rgba(191, 226, 208, 0.94);
}

.loading-text,
.empty-state {
  text-align: center;
  color: var(--text-muted);
  padding: 22px 0;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table th,
.table td {
  text-align: left;
  padding: 14px 10px;
  border-bottom: 1px solid rgba(215, 226, 234, 0.76);
  vertical-align: top;
}

.table th {
  color: #5f7081;
  font-weight: 700;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.badge-success {
  background: #e6f6ee;
  color: #1d6a42;
}

.badge-warning {
  background: #fff3d8;
  color: #8b6500;
}

.badge-danger {
  background: #fdecec;
  color: #9a2c2c;
}

.stat-value {
  font-size: 30px;
  font-weight: 800;
}

.stat-value.income {
  color: #1f8f5f;
}

.stat-value.expense {
  color: #d04d48;
}

.stat-value.balance {
  color: #1d6fdc;
}

@media (max-width: 1080px) {
  .navbar {
    grid-template-columns: 1fr;
    justify-items: stretch;
  }

  .navbar-links {
    justify-content: flex-start;
  }

  .navbar-actions {
    justify-content: space-between;
  }
}

@media (max-width: 720px) {
  .app-shell-header {
    padding: 12px 12px 0;
  }

  .main-content {
    padding: 22px 12px 36px;
  }

  .navbar {
    padding: 14px;
    border-radius: 20px;
  }

  .navbar-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .locale-switcher {
    align-self: flex-start;
  }

  .user-email {
    word-break: break-all;
  }

  .card {
    padding: 18px;
    border-radius: 20px;
  }

  .page-header h1 {
    font-size: 28px;
  }
}
</style>
