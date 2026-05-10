import { defineStore } from 'pinia'
import type { LoginInfo, InitInfo } from '@/types/auth'
import { logout as logoutApi } from '@/api/auth-service'

interface AuthState {
  userInfo: Partial<LoginInfo> | null
  accessToken: string | null
  refreshToken: string | null
  security: InitInfo | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    userInfo: JSON.parse(localStorage.getItem('user_info') || 'null'),
    accessToken: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token'),
    security: JSON.parse(localStorage.getItem('security_rules') || 'null'),
  }),

  getters: {
    isLoggedIn: (state) => !!state.accessToken,
  },

  actions: {
    setAuth(loginInfo: LoginInfo) {
      const { accessToken, refreshToken, ...rest } = loginInfo
      this.userInfo = rest
      this.accessToken = accessToken
      this.refreshToken = refreshToken

      localStorage.setItem('user_info', JSON.stringify(rest))
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
    },

    setSecurity(initInfo: InitInfo) {
      this.security = initInfo
      localStorage.setItem('security_rules', JSON.stringify(initInfo))
    },

    setAccessToken(token: string) {
      this.accessToken = token
      localStorage.setItem('access_token', token)
    },

    async logout() {
      try {
        await logoutApi()
      } catch (error) {
        console.error('Logout API failed:', error)
      } finally {
        this.clearAuth()
      }
    },

    clearAuth() {
      this.userInfo = null
      this.accessToken = null
      this.refreshToken = null
      localStorage.removeItem('user_info')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },
  },
})
