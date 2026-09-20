import type {
  HealthResponse,
  OverviewStats,
  CategoryStat,
  PromotionStat,
  PriceRangeStat,
  PredictRequest,
  PredictResponse,
  ModelMetrics,
  FeatureImportanceResponse,
  RuleListResponse,
} from './types'

export const mockHealth: HealthResponse = {
  status: 'ok',
  service: 'product-return-analysis-api',
  model_loaded: true,
  model_version: 'dt-20260910-001',
  dependencies: {
    hdfs: { status: 'ok', root: '/project/product-return' },
    hbase: { status: 'ok', tables: ['pr_orders', 'pr_model_registry', 'pr_stats', 'pr_predictions'] },
  },
  degraded: false,
}

export const mockOverview: OverviewStats = {
  sample_count: 1000,
  returned_count: 183,
  return_rate: 0.183,
  category_count: 8,
  average_price: 299.5,
  average_freight: 8.2,
  updated_at: '2026-09-10T12:00:00Z',
}

export const mockCategoryStats: { items: CategoryStat[] } = {
  items: [
    { category: '服饰', sample_count: 320, returned_count: 74, return_rate: 0.23125 },
    { category: '电子产品', sample_count: 180, returned_count: 36, return_rate: 0.2 },
    { category: '食品', sample_count: 150, returned_count: 21, return_rate: 0.14 },
    { category: '家居', sample_count: 120, returned_count: 18, return_rate: 0.15 },
    { category: '美妆', sample_count: 90, returned_count: 15, return_rate: 0.1667 },
    { category: '图书', sample_count: 80, returned_count: 8, return_rate: 0.1 },
    { category: '运动', sample_count: 40, returned_count: 7, return_rate: 0.175 },
    { category: '其他', sample_count: 20, returned_count: 4, return_rate: 0.2 },
  ],
}

export const mockPromotionStats: { items: PromotionStat[]; data_version: string; updated_at: string } = {
  items: [
    { is_promotion: 0, sample_count: 680, returned_count: 102, return_rate: 0.15 },
    { is_promotion: 1, sample_count: 320, returned_count: 81, return_rate: 0.253125 },
  ],
  data_version: '20260910-001',
  updated_at: '2026-09-10T12:00:00Z',
}

export const mockPriceRangeStats: { items: PriceRangeStat[]; data_version: string; updated_at: string } = {
  items: [
    { price_range: '0-100', sample_count: 260, returned_count: 58, return_rate: 0.223 },
    { price_range: '100-300', sample_count: 380, returned_count: 65, return_rate: 0.171 },
    { price_range: '300-500', sample_count: 220, returned_count: 38, return_rate: 0.173 },
    { price_range: '500-1000', sample_count: 100, returned_count: 15, return_rate: 0.15 },
    { price_range: '1000+', sample_count: 40, returned_count: 7, return_rate: 0.175 },
  ],
  data_version: '20260910-001',
  updated_at: '2026-09-10T12:00:00Z',
}

export function mockPredict(req: PredictRequest): PredictResponse {
  const returned = req.is_promotion === 1 && req.price > 200 ? 1 : 0
  const prob = returned === 1 ? 0.72 : 0.28
  return {
    predicted_returned: returned,
    return_probability: prob,
    class_probabilities: {
      not_returned: 1 - prob,
      returned: prob,
    },
    model: 'decision-tree',
    model_version: '20260910-001',
  }
}

export const mockModelMetrics: ModelMetrics = {
  model: 'decision-tree',
  model_version: '20260910-001',
  accuracy: 0.84,
  precision: 0.63,
  recall: 0.58,
  f1: 0.60,
  confusion_matrix: [[145, 19], [23, 13]],
  train_samples: 800,
  test_samples: 200,
  returned_rate_test: 0.18,
}

export const mockFeatureImportance: FeatureImportanceResponse = {
  items: [
    { feature: 'category_服饰', importance: 0.31 },
    { feature: 'price', importance: 0.24 },
    { feature: 'is_promotion', importance: 0.18 },
    { feature: 'season_夏', importance: 0.15 },
    { feature: 'freight', importance: 0.12 },
  ],
}

export const mockRules: RuleListResponse = {
  items: [
    {
      rule_id: 'leaf-1',
      conditions: ['price <= 120.50', 'is_promotion = 0'],
      predicted_returned: 0,
      return_probability: 0.15,
      sample_count: 120,
    },
    {
      rule_id: 'leaf-2',
      conditions: ['price <= 120.50', 'is_promotion = 1'],
      predicted_returned: 1,
      return_probability: 0.68,
      sample_count: 65,
    },
    {
      rule_id: 'leaf-3',
      conditions: ['price > 120.50', 'category = 服饰'],
      predicted_returned: 1,
      return_probability: 0.71,
      sample_count: 86,
    },
    {
      rule_id: 'leaf-4',
      conditions: ['price > 120.50', 'category != 服饰', 'freight <= 10'],
      predicted_returned: 0,
      return_probability: 0.22,
      sample_count: 95,
    },
  ],
}
