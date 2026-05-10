/**
 * Standard response wrapper returned by the auth service.
 */
export interface ApiResponse<T> {
  code: string
  msg: string
  data?: T
}

/**
 * LoginInfo payload returned after a successful login.
 */
export interface LoginInfo {
  userId?: string
  userCode?: string
  userName?: string
  fiscal?: number
  token?: string
  isDefaultPwd?: number
}

/**
 * LoginDTO request body.
 */
export interface LoginRequest {
  userCode: string
  password: string
  fiscal: number
  captcha?: string
}
