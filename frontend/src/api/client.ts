import axios from 'axios'
import type { ApiError } from './types'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

export function parseApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? 0
    const detail = (error.response?.data as { detail?: string })?.detail ?? error.message

    return {
      message: detail,
      status,
      detail,
      isDegraded: status === 503,
      isModelNotLoaded: status === 503 && detail.includes('model'),
      isNetworkError: status === 0,
    }
  }

  return {
    message: (error as Error)?.message ?? '未知错误',
    status: 0,
    detail: (error as Error)?.message ?? '未知错误',
    isDegraded: false,
    isModelNotLoaded: false,
    isNetworkError: true,
  }
}

export default client
