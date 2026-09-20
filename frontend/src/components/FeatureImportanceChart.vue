<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { FeatureImportance } from '@/api/types'

echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  data: FeatureImportance[]
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function renderChart() {
  if (!chart) return

  const sorted = [...props.data].sort((a, b) => b.importance - a.importance)

  chart.setOption({
    title: { text: '特征重要性', left: 'center', textStyle: { fontSize: 15 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params: { name: string; value: number }[]) => {
        const p = params[0]
        if (!p) return ''
        return `${p.name}<br/>重要性: ${p.value.toFixed(4)}`
      },
    },
    grid: { left: '20%', right: '10%', bottom: '10%', top: '15%' },
    xAxis: {
      type: 'value',
      name: '重要性',
      max: Math.max(...sorted.map(d => d.importance)) * 1.1,
    },
    yAxis: {
      type: 'category',
      data: sorted.map(d => d.feature).reverse(),
      axisLabel: { fontSize: 12 },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map(d => d.importance).reverse(),
        itemStyle: {
          color: '#4080ff',
          borderRadius: [0, 4, 4, 0],
        },
        label: {
          show: true,
          position: 'right',
          formatter: (p: { value: number }) => p.value.toFixed(4),
        },
      },
    ],
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
  height: 320px;
  min-height: 320px;
}
</style>
