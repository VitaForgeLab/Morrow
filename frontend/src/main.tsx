import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './store/AuthContext.tsx'

// 四层包裹，从外到内各管一件事：
//   ConfigProvider —— AntD 全局配置（中文语言包）
//   BrowserRouter  —— 路由（管 URL 和页面的对应关系）
//   AuthProvider   —— 全局登录态（token 和当前用户）
//   App            —— 路由表
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  </StrictMode>,
)
