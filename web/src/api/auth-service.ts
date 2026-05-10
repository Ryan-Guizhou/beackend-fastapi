import request from '@/axios'
import type { ApiResponse, LoginInfo, LoginRequest } from '@/types/auth'

/**
 * Authenticates a user and returns the login snapshot used by the front end.
 */
export async function login(payload: LoginRequest) {
  return request<ApiResponse<LoginInfo>>('/auth/login', {
    method: 'POST',
    data: payload,
  })
}

/**
 * Logs out the current session.
 */
export async function logout() {
  return request<ApiResponse<void>>('/auth/logout', {
    method: 'POST',
  })
}
