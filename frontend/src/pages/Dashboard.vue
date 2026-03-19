<template>
  <div>
    <h1 style="font-size:22px; font-weight:700; margin-bottom:20px;">📊 Dashboard</h1>

    <!-- 載入中 -->
    <div v-if="store.loading" class="loading-text">載入中...</div>
    <div v-else-if="store.error" class="error-msg">{{ store.error }}</div>

    <template v-else-if="store.summary">
      <!-- 統計卡片 -->
      <div class="stats-grid">
        <div class="card stat-card">
          <div class="card-label">總收入</div>
          <div class="stat-value income">{{ fmt(store.summary.total_income) }}</div>
        </div>
        <div class="card stat-card">
          <div class="card-label">總支出</div>
          <div class="stat-value expense">{{ fmt(store.summary.total_expense) }}</div>
        </div>
        <div class="card stat-card">
          <div class="card-label">淨餘額</div>
          <div class="stat-value balance" :class="store.summary.net_balance >= 0 ? 'income' : 'expense'">
            {{ fmt(store.summary.net_balance) }}
          </div>
        </div>
      </div>

      <!-- 每月趨勢（ASCII 長條圖） -->
      <div class="card">
        <h2>每月收支趨勢</h2>
        <div v-if="store.summary.monthly_trend.length === 0" class="empty-state">尚無資料</div>
        <div v-else class="chart-container">
          <div
            v-for="item in store.summary.monthly_trend"
            :key="item.month"
            class="chart-row"
          >
            <span class="chart-label">{{ item.month }}</span>
            <div class="chart-bars">
              <div class="bar-wrap">
                <div
                  class="bar income-bar"
                  :style="{ width: barWidth(item.income) + 'px' }"
                ></div>
                <span class="bar-val">{{ fmt(item.income) }}</span>
              </div>
              <div class="bar-wrap">
                <div
                  class="bar expense-bar"
                  :style="{ width: barWidth(item.expense) + 'px' }"
                ></div>
                <span class="bar-val">{{ fmt(item.expense) }}</span>
              </div>
            </div>
          </div>
          <div class="chart-legend">
            <span class="legend-dot income-dot"></span>收入
            <span class="legend-dot expense-dot" style="margin-left:16px;"></span>支出
          </div>
        </div>
      </div>

      <!-- 各類別支出 -->
      <div class="card">
        <h2>支出類別分析</h2>
        <div v-if="store.summary.expense_by_category.length === 0" class="empty-state">尚無支出資料</div>
        <table v-else>
          <thead>
            <tr>
              <th>類別</th>
              <th>金額</th>
              <th>佔比</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in store.summary.expense_by_category" :key="item.category">
              <td>{{ item.category }}</td>
              <td>{{ fmt(item.amount) }}</td>
              <td>
                <div class="progress-bar-wrap">
                  <div
                    class="progress-bar"
                    :style="{ width: pct(item.amount, store.summary.total_expense) + '%' }"
                  ></div>
                  <span>{{ pct(item.amount, store.summary.total_expense).toFixed(1) }}%</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- AI 財務摘要 -->
      <div class="card">
        <h2>🤖 AI 財務摘要</h2>
        <div v-if="!store.aiSummary">
          <button class="btn btn-primary" @click="store.fetchAiSummary()">生成摘要</button>
        </div>
        <div v-else class="ai-summary-text">{{ store.aiSummary }}</div>
      </div>
    </template>

    <div v-else class="empty-state">無資料，請先新增記帳記錄並執行 seed_data.py</div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'

const store = useDashboardStore()

onMounted(() => store.fetchSummary())

// 格式化金額
function fmt(val) {
  return `NT$ ${Number(val).toLocaleString('zh-TW', { minimumFractionDigits: 0 })}`
}

// 計算長條圖寬度（最大 300px）
function barWidth(val) {
  const max = Math.max(
    ...store.summary.monthly_trend.map(m => Math.max(m.income, m.expense))
  )
  return max > 0 ? Math.round((val / max) * 300) : 0
}

// 計算百分比
function pct(val, total) {
  return total > 0 ? (val / total) * 100 : 0
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.card-label {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
}

/* 長條圖 */
.chart-container { padding: 8px 0; }

.chart-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 12px;
}

.chart-label {
  width: 70px;
  font-size: 13px;
  color: #666;
  flex-shrink: 0;
}

.chart-bars { display: flex; flex-direction: column; gap: 4px; }

.bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar {
  height: 14px;
  border-radius: 3px;
  min-width: 4px;
  transition: width 0.3s;
}

.income-bar  { background: #27ae60; }
.expense-bar { background: #e74c3c; }

.bar-val {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

.chart-legend {
  display: flex;
  align-items: center;
  margin-top: 12px;
  font-size: 12px;
  color: #666;
}

.legend-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 2px;
  margin-right: 4px;
}

.income-dot  { background: #27ae60; }
.expense-dot { background: #e74c3c; }

/* 進度條 */
.progress-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  height: 8px;
  background: #e74c3c;
  border-radius: 4px;
  min-width: 2px;
  max-width: 200px;
}

/* AI 摘要 */
.ai-summary-text {
  background: #f8f9fa;
  border-left: 4px solid #1a73e8;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-line;
  color: #444;
}
</style>
