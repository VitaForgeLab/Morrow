import { useState } from 'react'
import { Button, Card, Form, Input, Tabs, Typography, message } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../store/AuthContext.tsx'

type Mode = 'login' | 'register'

/** 登录 / 注册页（对应 PRD 的 F11）。两个表单切换，成功后写入 token 并跳 /chat */
export default function LoginPage() {
  const { user, login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState<Mode>('login')
  const [submitting, setSubmitting] = useState(false)

  // 已经登录的人不该停留在登录页
  if (user) return <Navigate to="/chat" replace />

  const onFinish = async (values: { username: string; password: string }) => {
    setSubmitting(true)
    try {
      if (mode === 'login') {
        await login(values.username, values.password)
      } else {
        await register(values.username, values.password)
      }
      message.success(mode === 'login' ? '登录成功' : '注册成功')
      navigate('/chat', { replace: true })
    } catch (err) {
      message.error(err instanceof Error ? err.message : '操作失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f2f5',
      }}
    >
      <Card style={{ width: 400, boxShadow: '0 2px 12px rgba(0,0,0,0.08)' }}>
        <Typography.Title level={3} style={{ textAlign: 'center', marginBottom: 4 }}>
          Morrow
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ textAlign: 'center' }}>
          超声检查知识助手
        </Typography.Paragraph>

        <Tabs
          centered
          activeKey={mode}
          onChange={(key) => setMode(key as Mode)}
          items={[
            { key: 'login', label: '登录' },
            { key: 'register', label: '注册' },
          ]}
        />

        <Form onFinish={onFinish} layout="vertical" requiredMark={false}>
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少 3 个字符' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              size="large"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少 6 位' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              size="large"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </Form.Item>

          <Button type="primary" htmlType="submit" block size="large" loading={submitting}>
            {mode === 'login' ? '登录' : '注册并进入'}
          </Button>
        </Form>
      </Card>
    </div>
  )
}
