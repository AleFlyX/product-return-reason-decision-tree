import client from './client'
import {
  mockHealth,
  mockOverview,
  mockCategoryStats,
  mockPromotionStats,
  mockPriceRangeStats,
  mockPredict,
  mockModelMetrics,
  mockFeatureImportance,
  mockRules,
} from './mock'
import type { PredictRequest } from './types'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const mockMap: Record<string, () => unknown> = {
  'GET /api/health': () => mockHealth,
  'GET /api/stats/overview': () => mockOverview,
  'GET /api/stats/by-category': () => mockCategoryStats,
  'GET /api/stats/by-promotion': () => mockPromotionStats,
  'GET /api/stats/by-price-range': () => mockPriceRangeStats,
  'GET /api/model/metrics': () => mockModelMetrics,
  'GET /api/model/features': () => mockFeatureImportance,
  'GET /api/model/rules': () => mockRules,
}

export function setupMock() {
  if (!USE_MOCK) return

  client.interceptors.request.use(async (config) => {
    const method = (config.method ?? 'get').toUpperCase()
    const url = config.url ?? ''
    const key = `${method} ${url.split('?')[0]}`

    if (key === 'POST /api/returns/predict') {
      const body = config.data as PredictRequest
      return Promise.reject({
        __isMock: true,
        data: mockPredict(body),
        status: 200,
      })
    }

    const mockFn = mockMap[key]
    if (mockFn) {
      return Promise.reject({
        __isMock: true,
        data: mockFn(),
        status: 200,
      })
    }

    return config
  })

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error?.__isMock) {
        return Promise.resolve({ data: error.data, status: error.status })
      }
      return Promise.reject(error)
    },
  )
}
