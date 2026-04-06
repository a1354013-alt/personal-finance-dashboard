<template>
  <div class="stocks-page p-4">
    <h1 class="text-2xl font-bold mb-6">股票投資模組</h1>

    <!-- 操作提示訊息 -->
    <div v-if="actionMessage" class="mb-4 p-3 bg-green-100 text-green-700 rounded-lg flex justify-between items-center">
      <span>{{ actionMessage }}</span>
      <button @click="actionMessage = ''" class="text-green-500 font-bold ml-2">×</button>
    </div>
    <div v-if="actionError" class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg flex justify-between items-center">
      <span>{{ actionError }}</span>
      <button @click="actionError = ''" class="text-red-500 font-bold ml-2">×</button>
    </div>

    <!-- 自選股清單區塊 -->
    <section class="mb-8 bg-white p-6 rounded-xl shadow-sm border">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold">我的自選股 (Watchlist)</h2>
        <button 
          @click="handleSyncAll" 
          :disabled="stockStore.syncLoading"
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 transition"
        >
          {{ stockStore.syncLoading ? '同步中...' : '同步最新價格' }}
        </button>
      </div>

      <!-- 新增自選股表單 -->
      <form @submit.prevent="handleAddWatchlist" class="flex gap-2 mb-6 p-4 bg-gray-50 rounded-lg">
        <input 
          v-model="newStockCode" 
          type="text" 
          placeholder="輸入代碼 (如 2330 或 AAPL)" 
          class="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
          required
        />
        <button 
          type="submit" 
          :disabled="isAdding"
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
        >
          {{ isAdding ? '處理中...' : '加入自選' }}
        </button>
      </form>

      <!-- 清單表格 -->
      <div v-if="stockStore.watchlistLoading" class="py-10 text-center text-gray-500">載入中...</div>
      <div v-else-if="stockStore.watchlist.length === 0" class="py-10 text-center text-gray-400 bg-gray-50 rounded-lg border border-dashed">
        目前尚無自選股資料
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left">
          <thead>
            <tr class="border-b text-gray-500 text-sm">
              <th class="pb-3 font-medium">代碼</th>
              <th class="pb-3 font-medium">最新價格</th>
              <th class="pb-3 font-medium">更新時間</th>
              <th class="pb-3 font-medium">狀態</th>
              <th class="pb-3 font-medium text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in stockStore.watchlist" :key="item.id" class="border-b hover:bg-gray-50 transition">
              <td class="py-4 font-bold text-indigo-600">{{ item.stock_code }}</td>
              <td class="py-4">
                <span v-if="item.price" class="text-lg font-mono">${{ item.price.toFixed(2) }}</span>
                <span v-else class="text-gray-400">尚未同步</span>
              </td>
              <td class="py-4 text-sm text-gray-500">
                {{ item.date || '-' }}
              </td>
              <td class="py-4">
                <span 
                  v-if="item.price_sync_status === 'failed'" 
                  class="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full"
                  title="抓取真實資料失敗"
                >
                  ⚠️ 同步失敗
                </span>
                <span v-else class="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">正常</span>
              </td>
              <td class="py-4 text-right">
                <button @click="handleDeleteWatchlist(item.id)" class="text-red-500 hover:underline text-sm">刪除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 股票篩選結果區塊 -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border">
        <h2 class="text-xl font-semibold mb-4 text-green-700">通過篩選 (Passed)</h2>
        <div v-if="stockStore.filterLoading" class="text-gray-400">分析中...</div>
        <ul v-else-if="stockStore.passedStocks.length > 0" class="space-y-3">
          <li v-for="s in stockStore.passedStocks" :key="s.stock_code" class="p-3 bg-green-50 rounded-lg border border-green-100 flex justify-between">
            <span class="font-bold">{{ s.stock_code }}</span>
            <span class="text-green-600 text-sm">符合所有規則</span>
          </li>
        </ul>
        <p v-else class="text-gray-400 text-sm italic">目前無符合條件之股票</p>
      </div>

      <div class="bg-white p-6 rounded-xl shadow-sm border">
        <h2 class="text-xl font-semibold mb-4 text-red-700">未通過 (Failed)</h2>
        <div v-if="stockStore.filterLoading" class="text-gray-400">分析中...</div>
        <div v-else-if="stockStore.failedStocks.length > 0" class="space-y-3">
          <div v-for="s in stockStore.failedStocks" :key="s.stock_code" class="p-3 bg-red-50 rounded-lg border border-red-100">
            <div class="font-bold mb-1">{{ s.stock_code }}</div>
            <ul class="text-xs text-red-500 list-disc list-inside">
              <li v-for="reason in s.fail_reasons" :key="reason">{{ reason }}</li>
            </ul>
          </div>
        </div>
        <p v-else class="text-gray-400 text-sm italic">目前無未通過之股票</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useStockStore } from '@/stores/stockStore'

const stockStore = useStockStore()
const newStockCode = ref('')
const isAdding = ref(false)
const actionMessage = ref('')
const actionError = ref('')

onMounted(() => {
  stockStore.fetchWatchlist()
  stockStore.fetchFilterResults()
})

const handleAddWatchlist = async () => {
  if (!newStockCode.value.trim()) return
  
  isAdding.value = true
  actionMessage.value = ''
  actionError.value = ''
  
  try {
    const res = await stockStore.addToWatchlist(newStockCode.value.trim())
    newStockCode.value = ''
    
    // 顯示後端回傳的同步狀態訊息
    if (res.price_sync_status === 'failed') {
      actionMessage.value = `已加入 ${res.stock_code}，但最新價格同步失敗。`
    } else {
      actionMessage.value = `成功加入 ${res.stock_code}。`
    }
  } catch (err) {
    actionError.value = err || '加入失敗，請稍後再試。'
  } finally {
    isAdding.value = false
  }
}

const handleDeleteWatchlist = async (id) => {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await stockStore.deleteFromWatchlist(id)
    actionMessage.value = '已成功刪除。'
  } catch (err) {
    actionError.value = err || '刪除失敗。'
  }
}

const handleSyncAll = async () => {
  actionMessage.value = ''
  actionError.value = ''
  try {
    const res = await stockStore.syncAllPrices()
    // 修正：使用後端回傳的 message 內容
    actionMessage.value = res.message || '價格同步完成。'
  } catch (err) {
    actionError.value = err || '同步失敗。'
  }
}
</script>
