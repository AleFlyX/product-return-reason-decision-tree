import client from './client'
import type { ModelMetrics, FeatureImportanceResponse, RuleListResponse } from './types'

export async function getModelMetrics(): Promise<ModelMetrics> {
  const { data } = await client.get<ModelMetrics>('/api/model/metrics')
  return data
}

export async function getFeatureImportance(): Promise<FeatureImportanceResponse> {
  const { data } = await client.get<FeatureImportanceResponse>('/api/model/features')
  return data
}

export async function getRules(limit = 20): Promise<RuleListResponse> {
  const { data } = await client.get<RuleListResponse>('/api/model/rules', { params: { limit } })
  return data
}
