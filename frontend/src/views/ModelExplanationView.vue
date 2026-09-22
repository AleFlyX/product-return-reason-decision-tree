<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getModelMetrics, getFeatureImportance, getRules } from '@/api/model'
import { parseApiError } from '@/api/client'
import type { ModelMetrics, FeatureImportance, DecisionRule, ApiError } from '@/api/types'
import MetricCard from '@/components/MetricCard.vue'
import FeatureImportanceChart from '@/components/FeatureImportanceChart.vue'
import ConfusionMatrix from '@/components/ConfusionMatrix.vue'
import RuleList from '@/components/RuleList.vue'
import RequestState from '@/components/RequestState.vue'

const metrics = ref<ModelMetrics | null>(null)
const features = ref<FeatureImportance[]>([])
const rules = ref<DecisionRule[]>([])
const loading = ref(true)
const error = ref<ApiError | null>(null)

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const [m, f, r] = await Promise.all([getModelMetrics(), getFeatureImportance(), getRules()])
    metrics.value = m
    features.value = f.items
    rules.value = r.items
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="model-explanation">
    <h2 class="page-title">模型解释</h2>

    <RequestState
      :loading="loading"
      :error="error"
      :empty="!metrics && !error"
      @retry="loadData"
    />

    <template v-if="metrics && !error">
      <div class="metrics-grid">
        <MetricCard label="Accuracy" :value="(metrics.accuracy * 100).toFixed(1)" suffix="%" highlight />
        <MetricCard label="Precision" :value="(metrics.precision * 100).toFixed(1)" suffix="%" />
        <MetricCard label="Recall" :value="(metrics.recall * 100).toFixed(1)" suffix="%" />
        <MetricCard label="F1 Score" :value="metrics.f1.toFixed(4)" highlight />
        <MetricCard label="训练集样本" :value="metrics.train_samples" />
        <MetricCard label="测试集样本" :value="metrics.test_samples" />
        <MetricCard label="模型版本" :value="metrics.model_version" />
        <MetricCard label="数据版本" :value="metrics.data_version || '未知'" />
        <MetricCard label="测试集退货率" :value="(metrics.returned_rate_test * 100).toFixed(1)" suffix="%" />
      </div>

      <div class="chart-card">
        <ConfusionMatrix :matrix="metrics.confusion_matrix" />
      </div>

      <div class="chart-card">
        <FeatureImportanceChart :data="features" />
      </div>

      <div class="chart-card">
        <h3 class="section-title">决策树规则</h3>
        <RuleList :rules="rules" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.model-explanation {
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
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
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
</style>
