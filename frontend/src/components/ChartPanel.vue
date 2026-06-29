<template>
  <section class="card chart-panel">
    <div class="chart-header">
      <div>
        <h2>{{ title }}</h2>
        <p v-if="subtitle" class="chart-subtitle">{{ subtitle }}</p>
      </div>
    </div>

    <div v-if="loading" class="chart-skeleton">
      <div class="skeleton-bar" v-for="index in 6" :key="index" :style="{ height: `${40 + index * 10}px` }" />
    </div>
    <div v-else-if="error" class="chart-feedback chart-error-state">
      <div class="empty-visual">
        <span class="empty-ring" />
        <span class="empty-bars empty-bars-warning" />
      </div>
      <strong>{{ errorTitleComputed }}</strong>
      <p>{{ error }}</p>
    </div>
    <div v-else-if="!hasData" class="chart-feedback">
      <div class="empty-visual">
        <span class="empty-ring" />
        <span class="empty-bars" />
      </div>
      <strong>{{ emptyTitleComputed }}</strong>
      <p>{{ emptyDescriptionComputed }}</p>
    </div>
    <div v-else class="chart-body">
      <canvas ref="canvasRef" class="chart-canvas" />
    </div>
  </section>
</template>

<script setup>
import {
  Chart,
  ArcElement,
  BarController,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PieController,
  PointElement,
  Tooltip
} from 'chart.js'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

Chart.register(
  ArcElement,
  BarController,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PieController,
  PointElement,
  Tooltip
)

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  labels: { type: Array, default: () => [] },
  datasets: { type: Array, default: () => [] },
  type: { type: String, default: 'line' },
  emptyTitle: { type: String, default: '' },
  emptyDescription: { type: String, default: '' },
  errorTitle: { type: String, default: '' }
})

const { t } = useI18n()
const canvasRef = ref(null)
let chart = null

const hasData = computed(() => props.labels.length > 0 && props.datasets.some((dataset) => (dataset.data || []).length > 0))
const emptyTitleComputed = computed(() => props.emptyTitle || t('dashboard.empty.chartTitle'))
const emptyDescriptionComputed = computed(() => props.emptyDescription || t('dashboard.empty.chartDescription'))
const errorTitleComputed = computed(() => props.errorTitle || t('dashboard.errors.charts'))

function destroyChart() {
  if (!chart) return
  chart.destroy()
  chart = null
}

function renderChart() {
  destroyChart()
  if (!canvasRef.value || props.loading || props.error || !hasData.value) return

  chart = new Chart(canvasRef.value, {
    type: props.type,
    data: {
      labels: props.labels,
      datasets: props.datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            usePointStyle: true,
            boxWidth: 10,
            color: '#526170',
            padding: 18
          }
        },
        tooltip: {
          backgroundColor: '#163043',
          padding: 12,
          cornerRadius: 12
        }
      },
      layout: {
        padding: {
          top: 8,
          right: 8,
          bottom: 0,
          left: 4
        }
      },
      scales: props.type === 'pie'
        ? {}
        : {
            y: {
              beginAtZero: true,
              ticks: { color: '#6e7d8a' },
              grid: { color: 'rgba(90, 111, 132, 0.12)', drawBorder: false }
            },
            x: {
              ticks: { color: '#6e7d8a' },
              grid: { display: false, drawBorder: false }
            }
          }
    }
  })
}

async function scheduleRender() {
  await nextTick()
  renderChart()
}

watch(
  () => [props.loading, props.error, props.labels, props.datasets, props.type],
  scheduleRender,
  { deep: true, flush: 'post' }
)

onMounted(scheduleRender)
onBeforeUnmount(() => {
  destroyChart()
})
</script>

<style scoped>
.chart-panel {
  min-height: 312px;
  display: grid;
  grid-template-rows: auto 1fr;
}

.chart-header {
  margin-bottom: 12px;
}

.chart-subtitle {
  margin: 6px 0 0;
  color: #6d7d8b;
  font-size: 14px;
}

.chart-body {
  position: relative;
  min-height: 250px;
}

.chart-canvas {
  width: 100%;
  min-height: 250px;
}

.chart-skeleton {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  min-height: 250px;
}

.skeleton-bar {
  flex: 1;
  border-radius: 14px 14px 4px 4px;
  background: linear-gradient(180deg, rgba(193, 210, 224, 0.95) 0%, rgba(239, 244, 248, 0.78) 100%);
  animation: pulse 1.4s ease-in-out infinite;
}

.chart-feedback {
  min-height: 250px;
  display: grid;
  place-items: center;
  gap: 10px;
  text-align: center;
  padding: 20px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(248, 250, 246, 0.9) 0%, rgba(241, 246, 249, 0.96) 100%);
  border: 1px dashed rgba(136, 157, 176, 0.4);
}

.chart-feedback strong {
  font-size: 16px;
  color: #213645;
}

.chart-feedback p {
  margin: 0;
  max-width: 320px;
  color: #687887;
  line-height: 1.65;
}

.chart-error-state {
  background: linear-gradient(180deg, rgba(253, 247, 244, 0.95) 0%, rgba(250, 242, 239, 0.96) 100%);
  border-color: rgba(218, 154, 126, 0.4);
}

.empty-visual {
  position: relative;
  width: 76px;
  height: 76px;
}

.empty-ring {
  position: absolute;
  inset: 0;
  border-radius: 24px;
  background: radial-gradient(circle at 30% 30%, rgba(178, 225, 214, 0.72), rgba(178, 225, 214, 0) 56%),
    linear-gradient(135deg, rgba(234, 241, 247, 0.96), rgba(217, 228, 237, 0.85));
  box-shadow: inset 0 0 0 1px rgba(165, 183, 198, 0.4);
}

.empty-bars,
.empty-bars::before,
.empty-bars::after {
  position: absolute;
  bottom: 16px;
  width: 10px;
  border-radius: 999px;
  background: #5d89a8;
  content: '';
}

.empty-bars {
  left: 21px;
  height: 18px;
}

.empty-bars::before {
  left: 16px;
  height: 28px;
}

.empty-bars::after {
  left: 32px;
  height: 38px;
}

.empty-bars-warning,
.empty-bars-warning::before,
.empty-bars-warning::after {
  background: #d27f56;
}

@keyframes pulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 1; }
}

@media (max-width: 640px) {
  .chart-panel {
    min-height: 284px;
  }

  .chart-body,
  .chart-canvas,
  .chart-skeleton,
  .chart-feedback {
    min-height: 216px;
  }
}
</style>
