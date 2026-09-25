import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 把 /api 开头的请求转发给后端。
    // 浏览器看到的是"同源"（都是 localhost:5173），所以完全不涉及 CORS。
    // 生产环境由 Nginx 做同一件事，因此前端代码里始终写相对路径 /api/v1/...，
    // 开发和生产不用区分环境。
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
