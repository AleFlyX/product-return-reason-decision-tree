<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app">
    <nav class="nav-bar">
      <div class="nav-brand">
        <span class="brand-icon">DT</span>
        <span class="brand-text">商品退货原因分析系统</span>
      </div>
      <div class="nav-links">
        <RouterLink to="/" active-class="active">概览</RouterLink>
        <RouterLink to="/analysis" active-class="active">退货分析</RouterLink>
        <RouterLink to="/prediction" active-class="active">退货预测</RouterLink>
        <RouterLink to="/model" active-class="active">模型解释</RouterLink>
      </div>
    </nav>
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f5f6fa;
  color: #222;
}
</style>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 56px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #4080ff;
  color: #fff;
  border-radius: 8px;
  font-weight: 700;
  font-size: 14px;
}

.brand-text {
  font-size: 16px;
  font-weight: 600;
  color: #222;
}

.nav-links {
  display: flex;
  gap: 4px;
}

.nav-links a {
  padding: 8px 16px;
  border-radius: 6px;
  text-decoration: none;
  color: #666;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-links a:hover {
  background: #f0f5ff;
  color: #4080ff;
}

.nav-links a.active {
  background: #e6f0ff;
  color: #4080ff;
  font-weight: 600;
}

.main-content {
  flex: 1;
  padding: 24px 32px;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
}
</style>
