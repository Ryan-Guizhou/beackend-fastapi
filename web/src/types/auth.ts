/**
 * Standard response wrapper returned by the auth service.
 */
export interface ApiResponse<T> {
  code: string | number
  msg: string
  data?: T
}

/**
 * LoginInfo payload returned after a successful login.
 */
export interface LoginInfo {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  refreshExpiresIn?: number
  // Fields that might be added by AuthService._build_token_payload or similar
  userId?: string
  userCode?: string
  userName?: string
}

/**
 * Initialization info returned by the init endpoint.
 */
export interface InitInfo {
  sessionId: string
  rsaPublicKey: string
  rsaAlgorithm: string
  aesKey: string
  aesAlgorithm: string
  encoding: string
}

/**
 * LoginDTO request body.
 */
export interface LoginRequest {
  userCode: string
  password: string
  captcha: string
  sessionId: string
  fiscal?: number
}
