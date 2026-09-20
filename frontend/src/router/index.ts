import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'overview',
      component: () => import('@/views/OverviewView.vue'),
    },
    {
      path: '/analysis',
      name: 'analysis',
      component: () => import('@/views/ReturnAnalysisView.vue'),
    },
    {
      path: '/prediction',
      name: 'prediction',
      component: () => import('@/views/ReturnPredictionView.vue'),
    },
    {
      path: '/model',
      name: 'model',
      component: () => import('@/views/ModelExplanationView.vue'),
    },
  ],
})

export default router
