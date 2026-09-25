import { Navigate, Route, Routes } from 'react-router-dom'
import LoginPage from './pages/LoginPage.tsx'
import ChatPage from './pages/ChatPage.tsx'
import RequireAuth from './components/RequireAuth.tsx'

// 三条业务路由 + 一条兜底：
//   /login                  免登录
//   /chat                   聊天主页（未登录会被 RequireAuth 弹回 /login）
//   /chat/:conversationId   同上，但定位到指定会话
//   *                       无效地址一律导向 /chat
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/chat"
        element={
          <RequireAuth>
            <ChatPage />
          </RequireAuth>
        }
      />
      <Route
        path="/chat/:conversationId"
        element={
          <RequireAuth>
            <ChatPage />
          </RequireAuth>
        }
      />

      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  )
}
