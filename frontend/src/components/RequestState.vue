<script setup lang="ts">
import type { ApiError } from '@/api/types'

defineProps<{
  loading: boolean
  error: ApiError | null
  empty: boolean
}>()

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <div v-if="loading" class="state-box">
    <div class="spinner" />
    <span>加载中...</span>
  </div>
  <div v-else-if="error" class="state-box error">
    <span v-if="error.isNetworkError">网络连接失败，请检查后端服务是否启动</span>
    <span v-else-if="error.isModelNotLoaded">模型未加载，请联系管理员</span>
    <span v-else-if="error.isDegraded">数据服务不可用（HDFS/HBase 不可用）</span>
    <span v-else>{{ error.message }}</span>
    <button class="retry-btn" @click="emit('retry')">重试</button>
  </div>
  <div v-else-if="empty" class="state-box empty">
    <span>暂无数据</span>
  </div>
</template>

<style scoped>
.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 0;
  color: #999;
  min-height: 120px;
}

.error {
  color: #e74c3c;
}

.empty {
  color: #b0b0b0;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e0e0e0;
  border-top-color: #4080ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  padding: 6px 18px;
  border: 1px solid #4080ff;
  border-radius: 6px;
  background: #fff;
  color: #4080ff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: #4080ff;
  color: #fff;
}
</style>
