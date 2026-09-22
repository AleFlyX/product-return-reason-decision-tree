import client from './client'
import type { OverviewStats, CategoryStat, PromotionStat, PriceRangeStat } from './types'

export async function getOverviewStats(): Promise<OverviewStats> {
  const { data } = await client.get<OverviewStats>('/api/stats/overview')
  return data
}

export async function getCategoryStats(): Promise<{ items: CategoryStat[] }> {
  const { data } = await client.get<{ items: CategoryStat[] }>('/api/stats/by-category')
  return data
}

export async function getPromotionStats(): Promise<{ items: PromotionStat[]; data_version: string; updated_at: string }> {
  const { data } = await client.get('/api/stats/by-promotion')
  return data
}

export async function getPriceRangeStats(): Promise<{ items: PriceRangeStat[]; data_version: string; updated_at: string }> {
  const { data } = await client.get('/api/stats/by-price-range')
  return data
}
