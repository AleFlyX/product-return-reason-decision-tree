<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getCategoryStats, getPromotionStats, getPriceRangeStats } from '@/api/stats'
import { parseApiError } from '@/api/client'
import type { CategoryStat, PromotionStat, PriceRangeStat, ApiError } from '@/api/types'
import ReturnRateChart from '@/components/ReturnRateChart.vue'
import RequestState from '@/components/RequestState.vue'

const categoryData = ref<CategoryStat[]>([])
const promotionData = ref<PromotionStat[]>([])
const priceRangeData = ref<PriceRangeStat[]>([])
const loading = ref(true)
const error = ref<ApiError | null>(null)

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const [cat, promo, price] = await Promise.all([
      getCategoryStats(),
      getPromotionStats(),
      getPriceRangeStats(),
    ])
    categoryData.value = cat.items
    promotionData.value = promo.items
    priceRangeData.value = price.items
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    loading.value = false
  }
}

const priceRangeChartData = computed<CategoryStat[]>(() =>
  priceRangeData.value.map(d => ({
    category: d.price_range,
    sample_count: d.sample_count,
    returned_count: d.returned_count,
    return_rate: d.return_rate,
  })),
)

const promotionChartData = computed<CategoryStat[]>(() =>
  promotionData.value.map(d => ({
    category: d.is_promotion === 1 ? '促销' : '非促销',
    sample_count: d.sample_count,
    returned_count: d.returned_count,
    return_rate: d.return_rate,
  })),
)

const totalReturned = computed(() =>
  categoryData.value.reduce((sum, d) => sum + d.returned_count, 0),
)
const totalNotReturned = computed(() =>
  categoryData.value.reduce((sum, d) => sum + (d.sample_count - d.returned_count), 0),
)
const totalAll = computed(() => totalReturned.value + totalNotReturned.value)
const returnedPct = computed(() =>
  totalAll.value > 0 ? (totalReturned.value / totalAll.value) * 100 : 0,
)
const notReturnedPct = computed(() =>
  totalAll.value > 0 ? (totalNotReturned.value / totalAll.value) * 100 : 0,
)

onMounted(loadData)
</script>

<template>
  <div class="analysis">
    <h2 class="page-title">退货分析</h2>

    <RequestState
      :loading="loading"
      :error="error"
      :empty="!loading && categoryData.length === 0 && !error"
      @retry="loadData"
    />

    <template v-if="!loading && !error">
      <div class="chart-card">
        <ReturnRateChart v-if="categoryData.length" title="各类目退货率与样本量" :data="categoryData" />
        <div v-else class="no-data">暂无数据</div>
      </div>

      <div class="chart-card">
        <ReturnRateChart v-if="promotionChartData.length" title="促销 vs 非促销退货率" :data="promotionChartData" />
        <div v-else class="no-data">暂无数据</div>
      </div>

      <div class="chart-card">
        <ReturnRateChart v-if="priceRangeChartData.length" title="价格区间退货率" :data="priceRangeChartData" />
        <div v-else class="no-data">暂无数据</div>
      </div>

      <div v-if="totalAll > 0" class="chart-card summary">
        <h3 class="section-title">退货/未退货数量对比</h3>
        <div class="compare-bar">
          <div class="bar-item">
            <span class="bar-label">已退货</span>
            <div class="bar-bar returned" :style="{ width: `${returnedPct}%` }">
              {{ totalReturned }}
            </div>
          </div>
          <div class="bar-item">
            <span class="bar-label">未退货</span>
            <div class="bar-bar not-returned" :style="{ width: `${notReturnedPct}%` }">
              {{ totalNotReturned }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.analysis {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  padding: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
}

.summary {
  padding: 24px;
}

.compare-bar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-label {
  width: 60px;
  font-size: 13px;
  color: #666;
  flex-shrink: 0;
}

.bar-bar {
  height: 36px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-weight: 600;
  color: #fff;
  font-size: 14px;
  min-width: 40px;
  transition: width 0.3s;
}

.bar-bar.returned {
  background: #ff7875;
}

.bar-bar.not-returned {
  background: #52c41a;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #b0b0b0;
  font-size: 14px;
}
</style>
