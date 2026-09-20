<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([HeatmapChart, GridComponent, TooltipComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps<{
  matrix: number[][]
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

const labels = ['未退货 (0)', '退货 (1)']

const maxVal = computed(() => {
  let max = 0
  for (const row of props.matrix) {
    for (const val of row) {
      if (val > max) max = val
    }
  }
  return max
})

function renderChart() {
  if (!chart) return

  const data: [number, number, number][] = []
  for (let i = 0; i < props.matrix.length; i++) {
    const row = props.matrix[i]
    if (!row) continue
    for (let j = 0; j < row.length; j++) {
      data.push([j, i, row[j] ?? 0])
    }
  }

  chart.setOption({
    title: { text: '混淆矩阵', left: 'center', textStyle: { fontSize: 15 } },
    tooltip: {
      formatter: (p: { data: [number, number, number] }) => {
        const [actual, predicted, value] = p.data
        return `实际: ${labels[actual]}<br/>预测: ${labels[predicted]}<br/>样本数: ${value}`
      },
    },
    grid: { left: '15%', right: '15%', bottom: '15%', top: '15%' },
    xAxis: {
      type: 'category',
      name: '预测值',
      data: labels,
      splitArea: { show: true },
    },
    yAxis: {
      type: 'category',
      name: '实际值',
      data: labels,
      splitArea: { show: true },
    },
    visualMap: {
      min: 0,
      max: maxVal.value || 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: { color: ['#f0f5ff', '#69b1ff', '#1668dc'] },
    },
    series: [
      {
        type: 'heatmap',
        data,
        label: { show: true, fontSize: 16, fontWeight: 'bold' },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } },
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

watch(() => props.matrix, () => {
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
