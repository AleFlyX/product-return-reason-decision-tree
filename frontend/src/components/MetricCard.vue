<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  suffix?: string
  highlight?: boolean
}>()
</script>

<template>
  <div class="metric-card" :class="{ highlight }">
    <span class="label">{{ label }}</span>
    <span class="value">
      {{ value }}<span v-if="suffix" class="suffix">{{ suffix }}</span>
    </span>
  </div>
</template>

<style scoped>
.metric-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px 24px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  min-width: 140px;
}

.metric-card.highlight {
  border-left: 4px solid #4080ff;
}

.label {
  font-size: 13px;
  color: #888;
}

.value {
  font-size: 28px;
  font-weight: 700;
  color: #222;
  line-height: 1.2;
}

.suffix {
  font-size: 14px;
  font-weight: 400;
  color: #999;
  margin-left: 4px;
}
</style>
