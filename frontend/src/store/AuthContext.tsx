import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import * as authApi from '../api/auth.ts'
import { clearToken, getToken, setToken } from '../api/client.ts'
import type { UserOut } from '../types/api.ts'

/**
 * 全局登录态。
 *
 * 为什么用 Context 而不是把状态放在某个页面里？
 * 因为"当前用户是谁"要被多个页面/组件读到（聊天页要显示昵称、路由守卫要判断
 * 有没有登录）。Context 提供了一种"全局可读"的方式，不用一层层传 props。
 *
 * 这是 React 自带的机制，不需要引入 Redux（PRD 明确不引入）。
 */

interface AuthContextValue {
  user: UserOut | null
  /** 首次加载中：还在用 token 换用户信息，此时"有没有登录"还未知 */
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [loading, setLoading] = useState(true)

  // 刷新页面时：localStorage 里还有 token 的话，拿它换一次用户信息，
  // 确认这个 token 仍然有效（没被作废、没到期）。
  // 这一步让"刷新页面不掉登录"成立。
  useEffect(() => {
    if (!getToken()) {
      setLoading(false)
      return
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false))
  }, [])

  const login = async (username: string, password: string) => {
    const res = await authApi.login(username, password)
    setToken(res.access_token)
    setUser(res.user)
  }

  const register = async (username: string, password: string) => {
    const res = await authApi.register(username, password)
    setToken(res.access_token)
    setUser(res.user)
  }

  const logout = () => {
    clearToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

/** 任何组件里调用 useAuth() 就能拿到登录态，不用层层传 props */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth 必须在 AuthProvider 内部使用')
  return ctx
}
