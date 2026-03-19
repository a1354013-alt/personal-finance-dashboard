<template>
  <div>
    <h1 style="font-size:22px; font-weight:700; margin-bottom:20px;">📈 股票模組</h1>

    <!-- 自選股清單 -->
    <div class="card">
      <h2>自選股清單（Watchlist）</h2>
      <!-- 點 5: 使用拆分後的 watchlistLoading -->
      <div v-if="stockStore.watchlistLoading" class="loading-text">載入中...</div>
      <div v-else-if="stockStore.watchlist.length === 0" class="empty-state">尚無自選股</div>
      <table v-else>
        <thead>
          <tr>
            <th>代碼</th>
            <th>名稱</th>
            <th>股價</th>
            <th>日期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in stockStore.watchlist" :key="item.id">
            <td><strong>{{ item.stock_code }}</strong></td>
            <td>{{ item.name || '-' }}</td>
            <td style="font-weight:600; color:#1a73e8;">
              {{ item.price != null ? item.price.toLocaleString() : '-' }}
            </td>
            <td style="color:#888;">{{ item.date || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 股票篩選引擎結果 -->
    <div class="card">
      <h2>股票篩選引擎結果</h2>
      <p style="font-size:13px; color:#888; margin-bottom:14px;">
        規則：net_income &gt; 0 ｜ free_cash_flow &gt; 0 ｜ revenue_growth &gt; 0
      </p>

      <!-- 點 5: 使用拆分後的 filterLoading -->
      <div v-if="stockStore.filterLoading" class="loading-text">載入中...</div>
      <div v-else-if="stockStore.filterResults.length === 0" class="empty-state">尚無篩選結果</div>

      <template v-else>
        <!-- 通過篩選 -->
        <div style="margin-bottom:20px;">
          <div class="section-title pass-title">
            ✅ 通過篩選（{{ stockStore.passedStocks.length }} 支）
          </div>
          <table>
            <thead>
              <tr>
                <th>股票代碼</th>
                <th>狀態</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in stockStore.passedStocks" :key="s.stock_code">
                <td><strong>{{ s.stock_code }}</strong></td>
                <td><span class="badge badge-pass">通過</span></td>
              </tr>
              <tr v-if="stockStore.passedStocks.length === 0">
                <td colspan="2" class="empty-state">無通過股票</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 未通過篩選 -->
        <div>
          <div class="section-title fail-title">
            ❌ 未通過篩選（{{ stockStore.failedStocks.length }} 支）
          </div>
          <table>
            <thead>
              <tr>
                <th>股票代碼</th>
                <th>狀態</th>
                <th>失敗原因</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in stockStore.failedStocks" :key="s.stock_code">
                <td><strong>{{ s.stock_code }}</strong></td>
                <td><span class="badge badge-fail">未通過</span></td>
                <td>
                  <ul class="fail-reasons">
                    <li v-for="(reason, idx) in s.fail_reasons" :key="idx">{{ reason }}</li>
                  </ul>
                </td>
              </tr>
              <tr v-if="stockStore.failedStocks.length === 0">
                <td colspan="3" class="empty-state">無未通過股票</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>

    <!-- AI 股票解說 -->
    <div class="card">
      <h2>🤖 AI 股票解說</h2>
      <p style="font-size:13px; color:#888; margin-bottom:14px;">
        輸入股票基本面數據，取得 AI 分析解說
      </p>

      <div class="form-row">
        <div class="form-group">
          <label>股票代碼</label>
          <input v-model="explainForm.stock_code" type="text" placeholder="例：2330" />
        </div>
        <div class="form-group">
          <label>淨利潤</label>
          <input v-model.number="explainForm.net_income" type="number" placeholder="例：500000" />
        </div>
        <div class="form-group">
          <label>自由現金流</label>
          <input v-model.number="explainForm.free_cash_flow" type="number" placeholder="例：300000" />
        </div>
        <div class="form-group">
          <label>營收成長率 (%)</label>
          <input v-model.number="explainForm.revenue_growth" type="number" step="0.1" placeholder="例：12.5" />
        </div>
        <div class="form-group" style="justify-content:flex-end;">
          <button class="btn btn-primary" :disabled="aiLoading" @click="handleAiExplain">
            {{ aiLoading ? '分析中...' : '取得解說' }}
          </button>
        </div>
      </div>

      <div v-if="aiError" class="error-msg">{{ aiError }}</div>

      <div v-if="aiResult" class="ai-result">
        <div class="ai-result-header">
          <span class="badge" :class="aiResult.passed ? 'badge-pass' : 'badge-fail'">
            {{ aiResult.passed ? '通過篩選' : '未通過篩選' }}
          </span>
          <strong style="margin-left:8px;">{{ aiResult.stock_code }}</strong>
        </div>
        <div v-if="aiResult.fail_reasons.length > 0" style="margin:8px 0;">
          <span style="font-size:13px; color:#e74c3c;">失敗原因：</span>
          <ul class="fail-reasons">
            <li v-for="(r, i) in aiResult.fail_reasons" :key="i">{{ r }}</li>
          </ul>
        </div>
        <div class="ai-summary-text">{{ aiResult.explanation }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useStockStore } from '@/stores/stockStore'
// 點 6: 更新為獨立 API 模組引用路徑
import { getAiStockExplain } from '@/api/stocks'

const stockStore = useStockStore()

const explainForm = ref({
  stock_code: '2330',
  net_income: 500000,
  free_cash_flow: 300000,
  revenue_growth: 12.5,
})

const aiLoading = ref(false)
const aiError = ref('')
const aiResult = ref(null)

onMounted(() => {
  stockStore.fetchWatchlist()
  stockStore.fetchFilterResults()
})

async function handleAiExplain() {
  aiError.value = ''
  aiResult.value = null
  if (!explainForm.value.stock_code) {
    aiError.value = '請輸入股票代碼'
    return
  }
  aiLoading.value = true
  try {
    aiResult.value = await getAiStockExplain({ ...explainForm.value })
  } catch (e) {
    aiError.value = e.message
  } finally {
    aiLoading.value = false
  }
}
</script>

<style scoped>
.section-title {
  font-size: 14px;
  font-weight: 600;
  padding: 6px 10px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.pass-title { background: #d4edda; color: #155724; }
.fail-title { background: #f8d7da; color: #721c24; }

.fail-reasons {
  list-style: none;
  padding: 0;
  margin: 0;
}

.fail-reasons li {
  font-size: 12px;
  color: #c0392b;
  padding: 1px 0;
}

.fail-reasons li::before {
  content: '• ';
}

.ai-result {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
}

.ai-result-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.ai-summary-text {
  background: #fff;
  border-left: 4px solid #1a73e8;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-line;
  color: #444;
  margin-top: 8px;
}
</style>
