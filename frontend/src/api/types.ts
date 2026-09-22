export interface HealthResponse {
  status: string
  service: string
  model_loaded: boolean
  model_version: string
  dependencies: {
    hdfs: { status: string; root: string }
    hbase: { status: string; tables: string[] }
  }
  degraded: boolean
}

export interface OverviewStats {
  sample_count: number
  returned_count: number
  return_rate: number
  category_count: number
  average_price: number
  average_freight: number
  updated_at: string
}

export interface CategoryStat {
  category: string
  sample_count: number
  returned_count: number
  return_rate: number
}

export interface PromotionStat {
  is_promotion: number
  sample_count: number
  returned_count: number
  return_rate: number
}

export interface PriceRangeStat {
  price_range: string
  sample_count: number
  returned_count: number
  return_rate: number
}

export interface OrderItem {
  order_id: string
  category: string
  price: number
  is_promotion: number
  season: string
  freight: number
  returned: number
}

export interface OrderListResponse {
  items: OrderItem[]
  page: number
  page_size: number
  total: number
}

export interface PredictRequest {
  category: string
  price: number
  is_promotion: number
  season: string
  freight: number
}

export interface PredictResponse {
  predicted_returned: number
  return_probability: number
  class_probabilities: {
    not_returned: number
    returned: number
  }
  model: string
  model_version: string
}

export interface ModelMetrics {
  model: string
  model_version: string
  data_version?: string
  accuracy: number
  precision: number
  recall: number
  f1: number
  confusion_matrix: number[][]
  train_samples: number
  test_samples: number
  returned_rate_test: number
}

export interface FeatureImportance {
  feature: string
  importance: number
}

export interface FeatureImportanceResponse {
  items: FeatureImportance[]
}

export interface DecisionRule {
  rule_id: string
  conditions: string[]
  predicted_returned: number
  return_probability: number
  sample_count: number
}

export interface RuleListResponse {
  items: DecisionRule[]
}

export interface ApiError {
  message: string
  status: number
  detail: string
  isDegraded: boolean
  isModelNotLoaded: boolean
  isNetworkError: boolean
}
