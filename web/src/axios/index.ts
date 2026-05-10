import axios, { AxiosError, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import { refreshToken as refreshTokenApi } from '@/api/auth-service'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: Number(import.meta.env.VITE_REQUEST_TIMEOUT) || 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

let isRefreshing = false
let requests: any[] = []

request.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  // Only add accessToken if Authorization header is not already set (e.g., by refreshToken call)
  if (authStore.accessToken && !config.headers.Authorization) {
    config.headers.Authorization = authStore.accessToken
  }
  return config
})

request.interceptors.response.use(
  async (response: AxiosResponse) => {
    const code = String(response.data?.code ?? '')
    if (!code || code === '0' || code === '200') {
      return response
    }

    const authStore = useAuthStore()
    const errorMessage = response.data?.message || response.data?.msg || '请求失败'

    // Handle token expiration (402 indicates token expired)
    if (code === '401' || code === '40101' || code === '402') {
      const config = response.config

      if (!isRefreshing) {
        isRefreshing = true
        try {
          if (authStore.refreshToken) {
            const res = await refreshTokenApi(authStore.refreshToken)
            const newAccessToken = res.data?.data?.accessToken
            if (newAccessToken) {
              authStore.setAccessToken(newAccessToken)
              config.headers.Authorization = newAccessToken
              
              // Resend pending requests
              requests.forEach((cb) => cb(newAccessToken))
              requests = []
              return request(config)
            }
          }
        } catch (error) {
          authStore.clearAuth()
          window.location.href = '/login'
          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      } else {
        // Wait for token refresh
        return new Promise((resolve) => {
          requests.push((token: string) => {
            config.headers.Authorization = token
            resolve(request(config))
          })
        })
      }
    }

    message.error(errorMessage)
    return Promise.reject(new Error(errorMessage))
  },
  (error: AxiosError) => {
    if (!error.response) {
      const messageText = error.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络异常，请检查后重试'
      message.error(messageText)
      return Promise.reject(error)
    }

    const status = error.response.status
    const authStore = useAuthStore()

    if (status === 401) {
      authStore.clearAuth()
      window.location.href = '/login'
    }

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
    message.error(errorMessage)
    return Promise.reject(error)
  },
)

type RequestInstance = {
  <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
}

export default request as typeof request & RequestInstance
export type { AxiosRequestConfig, AxiosResponse }
