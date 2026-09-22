<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { CategoryStat } from '@/api/types'

echarts.use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{
  title: string
  data: CategoryStat[]
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function renderChart() {
  if (!chart) return
  if (!props.data || props.data.length === 0) {
    chart.clear()
    return
  }

  const sorted = [...props.data].sort((a, b) => b.return_rate - a.return_rate)

  chart.setOption({
    title: { text: props.title, left: 'center', textStyle: { fontSize: 15 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params: { name: string; value: number; dataIndex: number }[]) => {
        const p = params[0]
        if (!p) return ''
        const item = sorted[p.dataIndex]
        if (!item) return ''
        return `${item.category}<br/>退货率: ${(item.return_rate * 100).toFixed(1)}%<br/>样本量: ${item.sample_count}<br/>退货数: ${item.returned_count}`
      },
    },
    grid: { left: '8%', right: '8%', bottom: '15%', top: '15%' },
    xAxis: {
      type: 'category',
      data: sorted.map(d => d.category),
      axisLabel: { rotate: 30, fontSize: 12 },
    },
    yAxis: [
      {
        type: 'value',
        name: '退货率',
        axisLabel: { formatter: (val: number) => `${(val * 100).toFixed(0)}%` },
        max: 1,
      },
      {
        type: 'value',
        name: '样本量',
        position: 'right',
      },
    ],
    series: [
      {
        name: '退货率',
        type: 'bar',
        data: sorted.map(d => d.return_rate),
        itemStyle: { color: '#ff7875' },
        label: {
          show: true,
          position: 'top',
          formatter: (p: { dataIndex: number }) => {
            const item = sorted[p.dataIndex]
            return item ? `${(item.return_rate * 100).toFixed(1)}%` : ''
          },
        },
      },
      {
        name: '样本量',
        type: 'bar',
        yAxisIndex: 1,
        data: sorted.map(d => d.sample_count),
        itemStyle: { color: '#91d5ff', opacity: 0.5 },
        barGap: '20%',
      },
    ],
    legend: { data: ['退货率', '样本量'], top: 'bottom' },
  })
}

function handleResize() {
  chart?.resize()
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    renderChart()
    window.addEventListener('resize', handleResize)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})

watch(() => props.data, () => {
  nextTick(renderChart)
})
</script>

<template>
  <div ref="chartRef" class="chart-container" />
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 360px;
  min-height: 360px;
}
</style>
