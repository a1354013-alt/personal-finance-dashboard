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
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="!hasData" class="empty-state">No data yet</div>
    <canvas v-else ref="canvasRef" class="chart-canvas" />
  </section>
</template>

<script setup>
import { Chart, ArcElement, CategoryScale, Filler, Legend, LineElement, LinearScale, PointElement, Tooltip } from 'chart.js'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

Chart.register(ArcElement, CategoryScale, Filler, Legend, LineElement, LinearScale, PointElement, Tooltip)

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  labels: { type: Array, default: () => [] },
  datasets: { type: Array, default: () => [] },
  type: { type: String, default: 'line' }
})

const canvasRef = ref(null)
let chart = null

const hasData = computed(() => props.labels.length > 0 && props.datasets.some((dataset) => (dataset.data || []).length > 0))

function renderChart() {
  if (!canvasRef.value || props.loading || props.error || !hasData.value) return
  if (chart) chart.destroy()

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
          display: props.type !== 'pie',
          position: 'bottom'
        }
      },
      scales: props.type === 'pie'
        ? {}
        : {
            y: {
              beginAtZero: true,
              grid: { color: 'rgba(16, 43, 68, 0.08)' }
            },
            x: {
              grid: { display: false }
            }
          }
    }
  })
}

watch(() => [props.loading, props.error, props.labels, props.datasets, props.type], renderChart, { deep: true })
onMounted(renderChart)
onBeforeUnmount(() => {
  if (chart) chart.destroy()
})
</script>

<style scoped>
.chart-panel {
  min-height: 340px;
}

.chart-header {
  margin-bottom: 16px;
}

.chart-subtitle {
  margin: 6px 0 0;
  color: #66788a;
  font-size: 14px;
}

.chart-canvas {
  width: 100%;
  min-height: 260px;
}

.chart-skeleton {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  min-height: 260px;
}

.skeleton-bar {
  flex: 1;
  border-radius: 12px 12px 0 0;
  background: linear-gradient(180deg, rgba(209, 222, 236, 0.95) 0%, rgba(238, 244, 249, 0.7) 100%);
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 1; }
}
</style>
