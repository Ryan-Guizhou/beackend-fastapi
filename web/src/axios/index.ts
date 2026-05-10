import axios, { AxiosError, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { message } from 'ant-design-vue'

const TOKEN_KEY = import.meta.env.VITE_TOKEN_KEY || 'token'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: Number(import.meta.env.VITE_REQUEST_TIMEOUT) || 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = token
  }
  return config
})

request.interceptors.response.use(
  (response: AxiosResponse) => {
    const code = String(response.data?.code ?? '')
    if (!code || code === '0' || code === '200') {
      return response
    }

    const errorMessage = response.data?.message || response.data?.msg || '请求失败'
    if (code === '401' || code === '40101') {
      localStorage.removeItem(TOKEN_KEY)
      message.error('登录已过期，请重新登录')
      window.location.href = '/login'
    } else {
      message.error(errorMessage)
    }

    return Promise.reject(new Error(errorMessage))
  },
  (error: AxiosError) => {
    if (!error.response) {
      const messageText = error.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络异常，请检查后重试'
      message.error(messageText)
      return Promise.reject(error)
    }

    const status = error.response.status
    const errorMap: Record<number, string> = {
      400: '请求参数错误',
      401: '登录已过期，请重新登录',
      403: '没有权限访问该资源',
      404: '请求的资源不存在',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务不可用',
    }

    const errorMessage = errorMap[status] || `请求失败 (${status})`
    if (status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      window.location.href = '/login'
    }
    message.error(errorMessage)
    return Promise.reject(error)
  },
)

type RequestInstance = {
  <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
}

export default request as typeof request & RequestInstance
export type { AxiosRequestConfig, AxiosResponse }
