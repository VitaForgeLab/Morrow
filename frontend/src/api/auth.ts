import { request } from './client.ts'
import type { AuthResponse, UserOut } from '../types/api.ts'

/** 注册。收 JSON，成功后直接拿到 token（= 自动登录） */
export function register(username: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: { username, password },
    auth: false,
  })
}

/**
 * 登录。⚠️ 收的是【表单】，不是 JSON。
 * 这是 OAuth2 密码流规范要求的，所以这里用 form 而不是 body。
 */
export function login(username: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/login', {
    method: 'POST',
    form: { username, password },
    auth: false,
  })
}

/** 取当前登录用户。没有 token 或 token 失效会走到 client 里的 401 分支 */
export function me(): Promise<UserOut> {
  return request<UserOut>('/auth/me')
}
