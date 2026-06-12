import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import { createI18nInstance } from '@/i18n'

const { chartInstances } = vi.hoisted(() => ({
  chartInstances: []
}))

vi.mock('chart.js', () => {
  class MockChart {
    constructor(canvas, config) {
      this.canvas = canvas
      this.config = config
      this.destroy = vi.fn()
      chartInstances.push(this)
    }

    static register(...items) {
      void items
    }
  }

  return {
    Chart: MockChart,
    ArcElement: { id: 'ArcElement' },
    BarController: { id: 'BarController' },
    BarElement: { id: 'BarElement' },
    CategoryScale: { id: 'CategoryScale' },
    Filler: { id: 'Filler' },
    Legend: { id: 'Legend' },
    LineController: { id: 'LineController' },
    LineElement: { id: 'LineElement' },
    LinearScale: { id: 'LinearScale' },
    PieController: { id: 'PieController' },
    PointElement: { id: 'PointElement' },
    Tooltip: { id: 'Tooltip' }
  }
})

import ChartPanel from '@/components/ChartPanel.vue'

function mountChartPanel(props = {}) {
  return mount(ChartPanel, {
    props: {
      title: 'Chart',
      labels: ['Jan', 'Feb'],
      datasets: [{ label: 'Series', data: [10, 20] }],
      ...props
    },
    global: {
      plugins: [createI18nInstance()]
    }
  })
}

describe('ChartPanel', () => {
  beforeEach(() => {
    chartInstances.length = 0
  })

  it('renders the default line chart without throwing', () => {
    mountChartPanel()
    expect(chartInstances).toHaveLength(1)
    expect(chartInstances[0].config.type).toBe('line')
  })

  it('renders pie and bar charts without throwing', () => {
    mountChartPanel({ type: 'pie' })
    mountChartPanel({ type: 'bar' })

    expect(chartInstances).toHaveLength(2)
    expect(chartInstances[0].config.type).toBe('pie')
    expect(chartInstances[1].config.type).toBe('bar')
  })

  it('destroys the previous chart instance when switching to loading, error, or empty states', async () => {
    const wrapper = mountChartPanel()
    const firstChart = chartInstances[0]

    await wrapper.setProps({ loading: true })
    expect(firstChart.destroy).toHaveBeenCalledTimes(1)

    await wrapper.setProps({ loading: false, error: 'Failed to load' })
    expect(chartInstances).toHaveLength(1)

    await wrapper.setProps({ error: '', labels: [], datasets: [] })
    expect(chartInstances).toHaveLength(1)
  })
})
