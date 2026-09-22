<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { predictReturn } from '@/api/orders'
import { parseApiError } from '@/api/client'
import type { PredictResponse, ApiError } from '@/api/types'

const form = reactive({
  category: '',
  price: 0,
  is_promotion: 0,
  season: '',
  freight: 0,
})

const submitting = ref(false)
const result = ref<PredictResponse | null>(null)
const error = ref<ApiError | null>(null)
const validationErrors = ref<Record<string, string>>({})

const success = computed(() => result.value !== null && !error.value)

function validate(): boolean {
  validationErrors.value = {}

  if (!form.category) {
    validationErrors.value.category = '商品类目不能为空'
  }
  if (!form.season) {
    validationErrors.value.season = '季节不能为空'
  }
  if (form.price <= 0) {
    validationErrors.value.price = '价格必须大于0'
  }
  if (form.is_promotion !== 0 && form.is_promotion !== 1) {
    validationErrors.value.is_promotion = '促销状态只能为0或1'
  }
  if (form.freight < 0) {
    validationErrors.value.freight = '运费不能小于0'
  }

  return Object.keys(validationErrors.value).length === 0
}

async function submit() {
  if (!validate()) return

  submitting.value = true
  error.value = null
  result.value = null

  try {
    result.value = await predictReturn({ ...form })
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    submitting.value = false
  }
}

function reset() {
  result.value = null
  error.value = null
  validationErrors.value = {}
}
</script>

<template>
  <div class="prediction">
    <h2 class="page-title">退货预测</h2>

    <div class="form-card">
      <h3 class="section-title">输入订单信息</h3>
      <form @submit.prevent="submit" class="predict-form">
        <div class="form-row">
          <label class="form-label">
            <span>商品类目 <span class="required">*</span></span>
            <select v-model="form.category" :class="{ error: validationErrors.category }">
              <option value="">请选择</option>
              <option value="服饰">服饰</option>
              <option value="电子产品">电子产品</option>
              <option value="食品">食品</option>
              <option value="家居">家居</option>
              <option value="美妆">美妆</option>
              <option value="图书">图书</option>
              <option value="运动">运动</option>
              <option value="其他">其他</option>
            </select>
            <span v-if="validationErrors.category" class="err-msg">{{ validationErrors.category }}</span>
          </label>

          <label class="form-label">
            <span>商品价格 (元) <span class="required">*</span></span>
            <input
              v-model.number="form.price"
              type="number"
              min="0"
              step="0.01"
              :class="{ error: validationErrors.price }"
            />
            <span v-if="validationErrors.price" class="err-msg">{{ validationErrors.price }}</span>
          </label>
        </div>

        <div class="form-row">
          <label class="form-label">
            <span>是否促销 <span class="required">*</span></span>
            <select v-model.number="form.is_promotion" :class="{ error: validationErrors.is_promotion }">
              <option :value="0">非促销</option>
              <option :value="1">促销</option>
            </select>
            <span v-if="validationErrors.is_promotion" class="err-msg">{{ validationErrors.is_promotion }}</span>
          </label>

          <label class="form-label">
            <span>季节 <span class="required">*</span></span>
            <select v-model="form.season" :class="{ error: validationErrors.season }">
              <option value="">请选择</option>
              <option value="春">春</option>
              <option value="夏">夏</option>
              <option value="秋">秋</option>
              <option value="冬">冬</option>
            </select>
            <span v-if="validationErrors.season" class="err-msg">{{ validationErrors.season }}</span>
          </label>
        </div>

        <div class="form-row">
          <label class="form-label">
            <span>运费 (元) <span class="required">*</span></span>
            <input
              v-model.number="form.freight"
              type="number"
              min="0"
              step="0.01"
              :class="{ error: validationErrors.freight }"
            />
            <span v-if="validationErrors.freight" class="err-msg">{{ validationErrors.freight }}</span>
          </label>
        </div>

        <div class="form-actions">
          <button type="submit" class="submit-btn" :disabled="submitting">
            {{ submitting ? '预测中...' : '提交预测' }}
          </button>
          <button type="button" class="reset-btn" @click="reset">重置</button>
        </div>
      </form>
    </div>

    <div v-if="error" class="error-card">
      <span v-if="error.isNetworkError">网络连接失败，请检查后端服务是否启动</span>
      <span v-else-if="error.isDegraded && error.isModelNotLoaded">模型未加载，无法进行预测</span>
      <span v-else-if="error.isDegraded">数据服务不可用（HDFS/HBase 不可用）</span>
      <span v-else>{{ error.message }}</span>
    </div>

    <div v-if="success && result" class="result-card">
      <h3 class="section-title">预测结果</h3>
      <div class="result-badge" :class="result.predicted_returned === 1 ? 'returned' : 'not-returned'">
        {{ result.predicted_returned === 1 ? '退货' : '未退货' }}
      </div>
      <div class="result-grid">
        <div class="result-item">
          <span class="label">退货概率</span>
          <span class="value">{{ (result.return_probability * 100).toFixed(1) }}%</span>
        </div>
        <div class="result-item">
          <span class="label">未退货概率</span>
          <span class="value">{{ (result.class_probabilities.not_returned * 100).toFixed(1) }}%</span>
        </div>
        <div class="result-item">
          <span class="label">模型</span>
          <span class="value">{{ result.model }}</span>
        </div>
        <div class="result-item">
          <span class="label">模型版本</span>
          <span class="value">{{ result.model_version }}</span>
        </div>
      </div>
      <div class="probability-bar">
        <div class="bar returned" :style="{ width: `${result.return_probability * 100}%` }">
          退货 {{ (result.return_probability * 100).toFixed(1) }}%
        </div>
        <div class="bar not-returned" :style="{ width: `${result.class_probabilities.not_returned * 100}%` }">
          未退货 {{ (result.class_probabilities.not_returned * 100).toFixed(1) }}%
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.prediction {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}

.form-card,
.result-card,
.error-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  padding: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px;
}

.predict-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 20px;
}

.form-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.form-label > span:first-child {
  font-size: 13px;
  color: #666;
}

.required {
  color: #f5222d;
}

.form-label select,
.form-label input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-label select:focus,
.form-label input:focus {
  border-color: #4080ff;
}

.form-label select.error,
.form-label input.error {
  border-color: #f5222d;
}

.err-msg {
  font-size: 12px;
  color: #f5222d;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.submit-btn {
  padding: 8px 32px;
  background: #4080ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: #1677ff;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.reset-btn {
  padding: 8px 24px;
  background: #fff;
  color: #666;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.reset-btn:hover {
  border-color: #4080ff;
  color: #4080ff;
}

.error-card {
  color: #f5222d;
  text-align: center;
  padding: 20px;
}

.result-badge {
  display: inline-block;
  padding: 6px 24px;
  border-radius: 20px;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
}

.result-badge.returned {
  background: #fff1f0;
  color: #f5222d;
}

.result-badge.not-returned {
  background: #f6ffed;
  color: #52c41a;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-item .label {
  font-size: 13px;
  color: #888;
}

.result-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #222;
}

.probability-bar {
  display: flex;
  height: 40px;
  border-radius: 6px;
  overflow: hidden;
}

.bar {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  transition: width 0.3s;
  min-width: 30px;
}

.bar.returned {
  background: #ff7875;
}

.bar.not-returned {
  background: #52c41a;
}
</style>
