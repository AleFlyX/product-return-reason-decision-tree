<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getHealth } from '@/api/health'
import { getOverviewStats } from '@/api/stats'
import { parseApiError } from '@/api/client'
import type { HealthResponse, OverviewStats, ApiError } from '@/api/types'
import MetricCard from '@/components/MetricCard.vue'
import DependencyStatus from '@/components/DependencyStatus.vue'
import RequestState from '@/components/RequestState.vue'

const health = ref<HealthResponse | null>(null)
const stats = ref<OverviewStats | null>(null)
const loading = ref(true)
const error = ref<ApiError | null>(null)

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const [healthData, statsData] = await Promise.all([getHealth(), getOverviewStats()])
    health.value = healthData
    stats.value = statsData
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="overview">
    <h2 class="page-title">系统概览</h2>

    <RequestState
      :loading="loading"
      :error="error"
      :empty="!stats && !error"
      @retry="loadData"
    />

    <template v-if="stats && !error">
      <div class="metrics-grid">
        <MetricCard label="订单总数" :value="stats.sample_count" />
        <MetricCard label="退货总数" :value="stats.returned_count" highlight />
        <MetricCard label="整体退货率" :value="(stats.return_rate * 100).toFixed(1)" suffix="%" highlight />
        <MetricCard label="商品类目数" :value="stats.category_count" />
        <MetricCard label="平均商品价格" :value="stats.average_price.toFixed(1)" suffix="元" />
        <MetricCard label="平均运费" :value="stats.average_freight.toFixed(1)" suffix="元" />
      </div>

      <div class="dep-section">
        <h3 class="section-title">依赖与服务状态</h3>
        <DependencyStatus :health="health" />
      </div>

      <div class="updated">
        数据更新时间: {{ new Date(stats.updated_at).toLocaleString('zh-CN') }}
      </div>
    </template>
  </div>
</template>

<style scoped>
.overview {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.dep-section {
  padding: 20px 24px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
}

.updated {
  font-size: 13px;
  color: #999;
}
</style>
