<template>
  <div id="app-wrapper">
    <!-- 頂部導覽列 (僅登入後顯示) -->
    <nav class="navbar" v-if="authStore.isAuthenticated">
      <div class="navbar-brand">💰 Finance Dashboard v{{ VERSION }}</div>
      <ul class="navbar-links">
        <li><router-link to="/" exact-active-class="active">Dashboard</router-link></li>
        <li><router-link to="/expenses" active-class="active">記帳</router-link></li>
        <li><router-link to="/budgets" active-class="active">預算</router-link></li>
        <li><router-link to="/stocks" active-class="active">股票</router-link></li>
      </ul>
      <div class="navbar-user">
        <span class="user-email" v-if="authStore.user">{{ authStore.user.email }}</span>
        <button class="btn btn-logout" @click="handleLogout">登出</button>
      </div>
    </nav>

    <!-- 頁面內容 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { VERSION } from '@/constants/version'

const authStore = useAuthStore()
const router = useRouter()

// App 初始化時恢復認證狀態
onMounted(async () => {
  if (authStore.token && !authStore.user) {
    try {
      await authStore.fetchMe()
    } catch (e) {
      console.error('Session expired')
      router.push('/login')
    }
  }
})

function handleLogout() {
  if (confirm('確定要登出嗎？')) {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style>
/* ── 全域樣式 ── */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5;
  color: #333;
}

#app-wrapper {
  min-height: 100vh;
}

/* ── 導覽列 ── */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1a1a2e;
  color: #fff;
  padding: 0 24px;
  height: 56px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.navbar-brand {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.navbar-links {
  list-style: none;
  display: flex;
  gap: 8px;
}

.navbar-links a {
  color: #ccc;
  text-decoration: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 14px;
  transition: background 0.2s, color 0.2s;
}

.navbar-links a:hover,
.navbar-links a.active {
  background: #16213e;
  color: #fff;
}

.navbar-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-email {
  font-size: 12px;
  color: #aaa;
}

.btn-logout {
  background: #e74c3c;
  color: #fff;
  padding: 4px 12px;
  font-size: 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
}

/* ── 主內容區 ── */
.main-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px;
}

/* ── 通用卡片 ── */
.card {
  background: #fff;
  border-radius: 10px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  margin-bottom: 20px;
}

.card h2 {
  font-size: 16px;
  font-weight: 600;
  color: #555;
  margin-bottom: 12px;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

/* ── 統計數字 ── */
.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-value.income  { color: #27ae60; }
.stat-value.expense { color: #e74c3c; }
.stat-value.balance { color: #2980b9; }

/* ── 表格 ── */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
}

th {
  background: #f8f9fa;
  color: #666;
  font-weight: 600;
}

tr:hover td { background: #fafafa; }

/* ── 按鈕 ── */
.btn {
  display: inline-block;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: opacity 0.2s;
}

.btn:hover { opacity: 0.85; }
.btn-primary   { background: #1a73e8; color: #fff; }
.btn-success   { background: #27ae60; color: #fff; }
.btn-danger    { background: #e74c3c; color: #fff; }
.btn-secondary { background: #95a5a6; color: #fff; }

/* ── 表單 ── */
.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  align-items: flex-end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 140px;
}

.form-group label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: #1a73e8;
}

/* ── 標籤 ── */
.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.badge-income  { background: #d4edda; color: #155724; }
.badge-expense { background: #f8d7da; color: #721c24; }
.badge-pass    { background: #d4edda; color: #155724; }
.badge-fail    { background: #f8d7da; color: #721c24; }

/* ── 錯誤提示 ── */
.error-msg {
  color: #e74c3c;
  font-size: 13px;
  padding: 8px 12px;
  background: #fdf0f0;
  border-radius: 6px;
  margin-bottom: 12px;
}

/* ── 載入中 ── */
.loading-text {
  color: #999;
  font-size: 14px;
  padding: 20px 0;
  text-align: center;
}

/* ── 空狀態 ── */
.empty-state {
  text-align: center;
  color: #aaa;
  padding: 40px 0;
  font-size: 14px;
}

/* ── 進度條 (v0.6.0) ── */
.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin: 8px 0;
}

.progress-fill {
  height: 100%;
  transition: width 0.4s ease;
}

.bg-success { background-color: #28a745; }
.bg-warning { background-color: #ffc107; }
.bg-danger  { background-color: #dc3545; }
</style>
