<script setup lang="ts">
import type { DecisionRule } from '@/api/types'

defineProps<{
  rules: DecisionRule[]
}>()
</script>

<template>
  <div class="rule-list">
    <div v-for="rule in rules" :key="rule.rule_id" class="rule-card">
      <div class="rule-header">
        <span class="rule-id">{{ rule.rule_id }}</span>
        <span class="rule-badge" :class="rule.predicted_returned === 1 ? 'returned' : 'not-returned'">
          {{ rule.predicted_returned === 1 ? '退货' : '未退货' }}
        </span>
      </div>
      <ul class="conditions">
        <li v-for="(cond, idx) in rule.conditions" :key="idx">{{ cond }}</li>
      </ul>
      <div class="rule-footer">
        <span>退货概率: {{ (rule.return_probability * 100).toFixed(1) }}%</span>
        <span>样本量: {{ rule.sample_count }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rule-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rule-card {
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fafafa;
}

.rule-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.rule-id {
  font-weight: 700;
  color: #222;
  font-size: 14px;
}

.rule-badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.rule-badge.returned {
  background: #fff1f0;
  color: #f5222d;
}

.rule-badge.not-returned {
  background: #f6ffed;
  color: #52c41a;
}

.conditions {
  list-style: none;
  padding: 0;
  margin: 0 0 8px;
}

.conditions li {
  padding: 4px 0;
  font-size: 13px;
  color: #555;
  font-family: monospace;
}

.conditions li::before {
  content: '→ ';
  color: #b0b0b0;
}

.rule-footer {
  display: flex;
  gap: 24px;
  font-size: 12px;
  color: #999;
}
</style>
