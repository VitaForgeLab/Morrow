/**
 * fetch 的统一封装。整个前端只有这一个地方直接调用 fetch。
 *
 * 它负责四件事：
 *   1. 统一拼前缀 /api/v1（配合 Vite 代理，不用写完整域名）
 *   2. 自动带上 Authorization: Bearer <token>
 *   3. 自动解开后端信封，直接把 data 交给调用方
 *   4. 401 统一处理：清 token、跳登录页
 */

const BASE = '/api/v1'
const TOKEN_KEY = 'morrow_token'

/* ---------- token 的读写（存 localStorage） ---------- */

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

/* ---------- 错误类型 ---------- */

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/* ---------- 主函数 ---------- */

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  /** JSON 请求体 */
  body?: unknown
  /** 表单请求体（登录接口用，OAuth2 规范要求表单而不是 JSON） */
  form?: Record<string, string>
  /** 是否附带 token，默认 true。注册/登录要传 false */
  auth?: boolean
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, form, auth = true } = options

  const headers: Record<string, string> = {}
  let payload: string | undefined

  if (form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    payload = new URLSearchParams(form).toString()
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  if (auth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(BASE + path, { method, headers, body: payload })

  // 登录态失效：清掉 token 并弹回登录页（正在登录页时就不跳，避免循环）
  if (response.status === 401) {
    clearToken()
    if (window.location.pathname !== '/login') {
      window.location.replace('/login')
    }
    throw new ApiError(401, '登录已失效，请重新登录')
  }

  // 后端即使报错也返回 JSON，所以这里几乎不会失败；兜一个空对象防崩
  const json = await response.json().catch(() => null)

  if (!response.ok) {
    const msg =
      (json && typeof json === 'object' && 'message' in json && String(json.message)) ||
      `请求失败（${response.status}）`
    throw new ApiError(response.status, msg)
  }

  // 带信封的接口：解开 data 再返回
  if (json && typeof json === 'object' && 'code' in json && 'data' in json) {
    return (json as { data: T }).data
  }

  // 扁平接口（登录 / 注册）：原样返回
  return json as T
}
