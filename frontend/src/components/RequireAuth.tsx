import { Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import type { ReactNode } from 'react'
import { useAuth } from '../store/AuthContext.tsx'

/**
 * 路由守卫：没登录就弹回 /login（对应 PRD 的 F15）。
 *
 * 为什么 loading 时要先转圈，而不是直接判"没登录"？
 * 因为"有没有登录"要等 /auth/me 回来才知道。这段时间如果直接跳登录页，
 * 用户刷新一下就会闪一下登录页再跳回来，体验很差。
 */
export default function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  return <>{children}</>
}
