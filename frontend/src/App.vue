<template>
  <div id="app-wrapper">
    <nav v-if="authStore.isAuthenticated" class="navbar">
      <div class="navbar-brand">Personal Finance Dashboard v{{ VERSION }}</div>

      <ul class="navbar-links">
        <li><router-link to="/" exact-active-class="active">Dashboard</router-link></li>
        <li><router-link to="/expenses" active-class="active">Expenses</router-link></li>
        <li><router-link to="/budgets" active-class="active">Budgets</router-link></li>
        <li><router-link to="/stocks" active-class="active">Stocks</router-link></li>
      </ul>

      <div class="navbar-user">
        <span v-if="authStore.user" class="user-email">{{ authStore.user.email }}</span>
        <button class="btn btn-danger" @click="handleLogout">Sign Out</button>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { VERSION } from '@/constants/version'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
const router = useRouter()

onMounted(async () => {
  if (authStore.token && !authStore.user) {
    const success = await authStore.fetchMe()
    if (!success) {
      router.push('/login')
    }
  }
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style>
:root {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #22303c;
  background: #f3f6fb;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: linear-gradient(180deg, #f8fbff 0%, #eef3f8 100%);
  color: #22303c;
}

a {
  color: inherit;
}

#app-wrapper {
  min-height: 100vh;
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  background: #18324a;
  color: #fff;
  box-shadow: 0 4px 18px rgba(24, 50, 74, 0.18);
}

.navbar-brand {
  font-size: 18px;
  font-weight: 700;
}

.navbar-links {
  display: flex;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.navbar-links a {
  display: inline-block;
  padding: 8px 14px;
  border-radius: 8px;
  text-decoration: none;
  color: #d4e0ea;
}

.navbar-links a.active,
.navbar-links a:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.navbar-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-email {
  font-size: 13px;
  color: #d4e0ea;
}

.main-content {
  max-width: 1120px;
  margin: 0 auto;
  padding: 28px 16px 40px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
}

.page-header p {
  margin: 0;
  color: #66788a;
}

.card {
  background: #fff;
  border-radius: 14px;
  padding: 20px 24px;
  box-shadow: 0 8px 24px rgba(31, 52, 74, 0.08);
  margin-bottom: 20px;
  border: 1px solid #e4ebf2;
}

.card h2 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  color: #22303c;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 8px 16px;
  border: 0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.btn:hover {
  opacity: 0.92;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #1d6fdc;
  color: #fff;
}

.btn-secondary {
  background: #73859a;
  color: #fff;
}

.btn-success {
  background: #1f8f5f;
  color: #fff;
}

.btn-danger {
  background: #d04d48;
  color: #fff;
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
  gap: 6px;
  min-width: 180px;
  flex: 1;
}

.form-group label {
  font-size: 13px;
  color: #546575;
  font-weight: 600;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cfdae5;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: 2px solid rgba(29, 111, 220, 0.18);
  border-color: #1d6fdc;
}

.error-msg {
  color: #9a2c2c;
  background: #fdecec;
  border: 1px solid #f4cccc;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  margin-bottom: 12px;
}

.success-msg {
  color: #1d6a42;
  background: #e8f7ef;
  border: 1px solid #c9ecd7;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  margin-bottom: 12px;
}

.loading-text,
.empty-state {
  text-align: center;
  color: #73859a;
  padding: 28px 0;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table th,
.table td {
  text-align: left;
  padding: 12px 10px;
  border-bottom: 1px solid #e7edf3;
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
  padding: 4px 10px;
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
  font-size: 28px;
  font-weight: 700;
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

@media (max-width: 840px) {
  .navbar {
    flex-direction: column;
    align-items: stretch;
  }

  .navbar-links {
    flex-wrap: wrap;
  }

  .navbar-user {
    justify-content: space-between;
  }
}
</style>
