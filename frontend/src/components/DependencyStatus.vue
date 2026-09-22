<script setup lang="ts">
import type { HealthResponse } from '@/api/types'

defineProps<{
  health: HealthResponse | null
}>()
</script>

<template>
  <div class="dependency-status">
    <div class="dep-item">
      <span class="dot" :class="health?.dependencies.hdfs.status === 'ok' ? 'ok' : 'down'" />
      <span class="label">HDFS</span>
      <span class="value">{{ health?.dependencies.hdfs.status === 'ok' ? '正常' : '不可用' }}</span>
      <span v-if="health?.dependencies.hdfs.status === 'ok'" class="detail">{{ health.dependencies.hdfs.root }}</span>
    </div>
    <div class="dep-item">
      <span class="dot" :class="health?.dependencies.hbase.status === 'ok' ? 'ok' : 'down'" />
      <span class="label">HBase</span>
      <span class="value">{{ health?.dependencies.hbase.status === 'ok' ? '正常' : '不可用' }}</span>
      <span v-if="health?.dependencies.hbase.status === 'ok'" class="detail">
        {{ health.dependencies.hbase.tables.join(', ') }}
      </span>
    </div>
    <div class="dep-item">
      <span class="dot" :class="health?.model_loaded ? 'ok' : 'warn'" />
      <span class="label">模型</span>
      <span class="value">{{ health?.model_loaded ? '已加载' : '未加载' }}</span>
      <span v-if="health?.model_loaded" class="detail">{{ health.model_version }}</span>
    </div>
    <div v-if="health?.degraded" class="dep-item">
      <span class="dot warn" />
      <span class="label">状态</span>
      <span class="value warn-text">降级模式</span>
    </div>
  </div>
</template>

<style scoped>
.dependency-status {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.dep-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.dot.ok { background: #52c41a; }
.dot.down { background: #f5222d; }
.dot.warn { background: #faad14; }

.label {
  color: #888;
}

.value {
  color: #222;
  font-weight: 600;
}

.warn-text {
  color: #faad14;
}

.detail {
  color: #b0b0b0;
  font-size: 12px;
}
</style>
