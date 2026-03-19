<template>
  <div>
    <h1 style="font-size:22px; font-weight:700; margin-bottom:20px;">📒 記帳系統</h1>

    <!-- 新增表單 -->
    <div class="card">
      <h2>新增記錄</h2>
      <div v-if="formError || store.error" class="error-msg">{{ formError || store.error }}</div>
      <div class="form-row">
        <div class="form-group">
          <label>金額 *</label>
          <input v-model.number="form.amount" type="number" min="0.01" step="0.01" placeholder="例：1500" />
        </div>
        <div class="form-group">
          <label>類型 *</label>
          <select v-model="form.type">
            <option value="income">收入</option>
            <option value="expense">支出</option>
          </select>
        </div>
        <div class="form-group">
          <label>類別 *</label>
          <input v-model="form.category" type="text" placeholder="例：餐飲、薪資" />
        </div>
        <div class="form-group">
          <label>日期 *</label>
          <input v-model="form.date" type="date" />
        </div>
        <div class="form-group" style="min-width:200px;">
          <label>備註</label>
          <input v-model="form.note" type="text" placeholder="選填" />
        </div>
        <div class="form-group" style="justify-content:flex-end;">
          <button class="btn btn-primary" :disabled="store.submitting" @click="handleAdd">
            {{ store.submitting ? '新增中...' : '+ 新增' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 篩選列 -->
    <div class="card" style="padding:14px 24px;">
      <div class="form-row" style="margin-bottom:0;">
        <div class="form-group">
          <label>篩選類型</label>
          <select v-model="filterType" @change="handleFilter">
            <option value="">全部</option>
            <option value="income">收入</option>
            <option value="expense">支出</option>
          </select>
        </div>
        <div class="form-group" style="justify-content:flex-end;">
          <button class="btn btn-secondary" @click="resetFilter">重置</button>
        </div>
      </div>
    </div>

    <!-- 記錄列表 -->
    <div class="card">
      <h2>
        記帳列表
        <span style="font-size:12px; color:#999; font-weight:400; margin-left:8px;">
          共 {{ store.expenses.length }} 筆
        </span>
      </h2>

      <div v-if="store.loading" class="loading-text">載入中...</div>
      <div v-else-if="store.expenses.length === 0" class="empty-state">目前尚無記錄</div>

      <table v-else>
        <thead>
          <tr>
            <th>日期</th>
            <th>類型</th>
            <th>類別</th>
            <th>金額</th>
            <th>備註</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in store.expenses" :key="item.id">
            <td>{{ item.date }}</td>
            <td>
              <span :class="['badge', item.type === 'income' ? 'badge-income' : 'badge-expense']">
                {{ item.type === 'income' ? '收入' : '支出' }}
              </span>
            </td>
            <td>{{ item.category }}</td>
            <td :style="{ color: item.type === 'income' ? '#27ae60' : '#e74c3c', fontWeight: 600 }">
              {{ item.type === 'income' ? '+' : '-' }}{{ Number(item.amount).toLocaleString() }}
            </td>
            <td style="color:#888;">{{ item.note || '-' }}</td>
            <td>
              <button class="btn btn-danger" style="padding:4px 10px; font-size:12px;" @click="handleDelete(item.id)">
                刪除
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 小計 -->
      <div v-if="store.expenses.length > 0" class="summary-row">
        <span>收入小計：<strong style="color:#27ae60;">{{ fmtAmt(store.totalIncome) }}</strong></span>
        <span>支出小計：<strong style="color:#e74c3c;">{{ fmtAmt(store.totalExpense) }}</strong></span>
        <span>
          淨餘額：
          <strong :style="{ color: store.totalIncome - store.totalExpense >= 0 ? '#27ae60' : '#e74c3c' }">
            {{ fmtAmt(store.totalIncome - store.totalExpense) }}
          </strong>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useExpenseStore } from '@/stores/expenseStore'

const store = useExpenseStore()
const filterType = ref('')
const formError = ref('')

const today = new Date().toISOString().split('T')[0]

const form = ref({
  amount: null,
  type: 'expense',
  category: '',
  date: today,
  note: '',
})

onMounted(() => store.fetchExpenses())

async function handleAdd() {
  formError.value = ''
  if (!form.value.amount || form.value.amount <= 0) {
    formError.value = '請輸入有效金額（必須大於 0）'
    return
  }
  if (!form.value.category.trim()) {
    formError.value = '請輸入類別'
    return
  }
  if (!form.value.date) {
    formError.value = '請選擇日期'
    return
  }
  try {
    await store.addExpense({ ...form.value })
    // 重置表單
    form.value = { amount: null, type: 'expense', category: '', date: today, note: '' }
  } catch (e) {
    // 錯誤會自動顯示在 store.error
  }
}

async function handleDelete(id) {
  if (!confirm('確定要刪除這筆記錄嗎？')) return
  // 點 3: 刪除失敗改為頁面內錯誤顯示 (與現有風格一致)
  try {
    await store.removeExpense(id)
  } catch (e) {
    // 錯誤已由 store.error 接管，會自動顯示在頁面上方的 error-msg
  }
}

function handleFilter() {
  store.fetchExpenses(filterType.value ? { type: filterType.value } : {})
}

function resetFilter() {
  filterType.value = ''
  store.fetchExpenses()
}

function fmtAmt(val) {
  return `NT$ ${Number(val).toLocaleString('zh-TW')}`
}
</script>

<style scoped>
.summary-row {
  display: flex;
  gap: 24px;
  padding: 12px 0 0;
  border-top: 1px solid #eee;
  margin-top: 8px;
  font-size: 14px;
  color: #555;
}
</style>
