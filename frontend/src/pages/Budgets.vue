<template>
  <div class="budgets-page p-4">
    <h1 class="text-2xl font-bold mb-6">預算管理 (v0.6.0)</h1>

    <!-- 訊息提示 -->
    <div v-if="message" class="mb-4 p-3 bg-green-100 text-green-700 rounded-lg flex justify-between items-center">
      <span>{{ message }}</span>
      <button @click="message = ''" class="font-bold ml-2">×</button>
    </div>
    <div v-if="error" class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg flex justify-between items-center">
      <span>{{ error }}</span>
      <button @click="error = ''" class="font-bold ml-2">×</button>
    </div>

    <!-- 新增預算表單 -->
    <section class="bg-white p-6 rounded-xl shadow-sm border mb-8">
      <h2 class="text-xl font-semibold mb-4">設定預算限額</h2>
      <form @submit.prevent="handleAddBudget" class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">消費類別</label>
          <select 
            v-model="newBudget.category" 
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
            required
          >
            <option value="" disabled>請選擇類別</option>
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">每月預算限額</label>
          <input 
            v-model.number="newBudget.monthly_limit" 
            type="number" 
            step="0.01"
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
            placeholder="例如 5000"
            required
          />
        </div>
        <div class="flex items-end">
          <button 
            type="submit" 
            :disabled="isSubmitting"
            class="w-full py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 transition"
          >
            {{ isSubmitting ? '處理中...' : '設定預算' }}
          </button>
        </div>
      </form>
    </section>

    <!-- 預算清單 -->
    <section class="bg-white p-6 rounded-xl shadow-sm border">
      <h2 class="text-xl font-semibold mb-6">預算執行進度 (當月)</h2>
      <div v-if="loading" class="text-center py-10 text-gray-500">載入中...</div>
      <div v-else-if="budgets.length === 0" class="text-center py-10 text-gray-400 bg-gray-50 rounded-lg border border-dashed">
        目前尚無預算設定
      </div>
      <div v-else class="space-y-6">
        <div v-for="budget in budgets" :key="budget.id" class="p-4 bg-gray-50 rounded-lg border">
          <div class="flex justify-between items-center mb-2">
            <div>
              <span class="font-bold text-lg text-indigo-700">{{ budget.category }}</span>
              <span class="ml-2 text-sm text-gray-500">預算: ${{ budget.monthly_limit }}</span>
            </div>
            <button @click="handleDeleteBudget(budget.id)" class="text-red-500 hover:text-red-700 text-sm">刪除</button>
          </div>
          
          <!-- 進度條 -->
          <div class="relative w-full h-4 bg-gray-200 rounded-full overflow-hidden mb-2">
            <div 
              class="absolute top-0 left-0 h-full transition-all duration-500"
              :class="budget.percent_used > 100 ? 'bg-red-500' : 'bg-green-500'"
              :style="{ width: Math.min(budget.percent_used, 100) + '%' }"
            ></div>
          </div>
          
          <div class="flex justify-between text-sm">
            <span :class="budget.percent_used > 100 ? 'text-red-600 font-bold' : 'text-gray-600'">
              已使用: ${{ budget.current_spent }} ({{ budget.percent_used.toFixed(1) }}%)
            </span>
            <span v-if="budget.percent_used > 100" class="text-red-600 font-bold animate-pulse">⚠️ 已超支!</span>
            <span v-else class="text-gray-500">剩餘: ${{ (budget.monthly_limit - budget.current_spent).toFixed(1) }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as budgetApi from '@/api/budgets'

const budgets = ref([])
const loading = ref(false)
const isSubmitting = ref(false)
const message = ref('')
const error = ref('')

const categories = ['餐飲', '交通', '購物', '娛樂', '醫療', '居住', '投資', '其他']

const newBudget = ref({
  category: '',
  monthly_limit: null
})

const fetchBudgets = async () => {
  loading.value = true
  try {
    budgets.value = await budgetApi.getBudgets()
  } catch (err) {
    error.value = '無法取得預算資料'
  } finally {
    loading.value = false
  }
}

const handleAddBudget = async () => {
  isSubmitting.value = true
  message.value = ''
  error.value = ''
  try {
    await budgetApi.createBudget(newBudget.value)
    message.value = '預算設定成功'
    newBudget.value = { category: '', monthly_limit: null }
    await fetchBudgets()
  } catch (err) {
    error.value = '設定失敗，請稍後再試'
  } finally {
    isSubmitting.value = false
  }
}

const handleDeleteBudget = async (id) => {
  if (!confirm('確定要刪除此預算設定嗎？')) return
  try {
    await budgetApi.deleteBudget(id)
    message.value = '已刪除預算設定'
    await fetchBudgets()
  } catch (err) {
    error.value = '刪除失敗'
  }
}

onMounted(fetchBudgets)
</script>
