import request from '@/axios'
import type { ApiResponse, InitInfo, LoginInfo, LoginRequest } from '@/types/auth'

/**
 * Initializes security rules (RSA/AES).
 */
export async function initSecurity() {
  return request<ApiResponse<InitInfo>>('/core/auth/init', {
    method: 'GET',
  })
}

/**
 * Authenticates a user and returns the login snapshot used by the front end.
 */
export async function login(payload: LoginRequest) {
  return request<ApiResponse<LoginInfo>>('/core/auth/login', {
    method: 'POST',
    data: payload,
  })
}

/**
 * Refreshes the access token using a refresh token.
 */
export async function refreshToken(token: string) {
  return request<ApiResponse<LoginInfo>>('/core/auth/refresh_token', {
    method: 'POST',
    headers: {
      Authorization: token,
    },
  })
}

/**
 * Logs out the current session.
 */
export async function logout() {
  return request<ApiResponse<void>>('/core/auth/logout', {
    method: 'POST',
  })
}
