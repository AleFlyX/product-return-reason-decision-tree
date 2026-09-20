import client from './client'
import type { OrderListResponse, PredictRequest, PredictResponse } from './types'

export async function getOrders(params: {
  page?: number
  page_size?: number
  category?: string
  returned?: number
}): Promise<OrderListResponse> {
  const { data } = await client.get<OrderListResponse>('/api/orders', { params })
  return data
}

export async function predictReturn(req: PredictRequest): Promise<PredictResponse> {
  const { data } = await client.post<PredictResponse>('/api/returns/predict', req)
  return data
}
