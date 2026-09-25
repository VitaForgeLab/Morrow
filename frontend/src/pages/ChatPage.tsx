import { useCallback, useEffect, useState } from 'react'
import { Button, Empty, Layout, Typography, message } from 'antd'
import { LogoutOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import * as api from '../api/conversations.ts'
import type { ConversationOut, MessageOut } from '../types/api.ts'
import { useAuth } from '../store/AuthContext.tsx'
import ConversationList from '../components/ConversationList.tsx'
import MessageList from '../components/MessageList.tsx'
import MessageInput from '../components/MessageInput.tsx'

const { Header, Sider, Content, Footer } = Layout

/** 聊天主页（对应 PRD 的 F12 / F13 / F14 / F16）。
 *  布局：顶栏 + [ 左会话列表 | 右消息区 ] + 底部免责声明 */
export default function ChatPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { conversationId } = useParams()

  const currentId = conversationId ? Number(conversationId) : null

  const [conversations, setConversations] = useState<ConversationOut[]>([])
  const [messages, setMessages] = useState<MessageOut[]>([])
  const [loadingMsgs, setLoadingMsgs] = useState(false)
  const [sending, setSending] = useState(false)
  const [streamingText, setStreamingText] = useState<string | null>(null)

  const refreshConversations = useCallback(async () => {
    const list = await api.listConversations()
    setConversations(list)
    return list
  }, [])

  // 进页面时拉会话列表；URL 里没指定会话就自动选中第一个
  useEffect(() => {
    refreshConversations()
      .then((list) => {
        if (!currentId && list.length > 0) {
          navigate(`/chat/${list[0].id}`, { replace: true })
        }
      })
      .catch((e) => message.error(e instanceof Error ? e.message : '加载会话失败'))
    // 只在首次进入时跑
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 切换会话时拉该会话的消息历史
  useEffect(() => {
    if (!currentId) {
      setMessages([])
      return
    }
    setLoadingMsgs(true)
    api
      .listMessages(currentId)
      .then(setMessages)
      .catch((e) => message.error(e instanceof Error ? e.message : '加载消息失败'))
      .finally(() => setLoadingMsgs(false))
  }, [currentId])

  const handleCreate = async () => {
    try {
      const conv = await api.createConversation()
      setConversations((prev) => [conv, ...prev])
      navigate(`/chat/${conv.id}`)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '新建失败')
    }
  }

  const handleRename = async (id: number, title: string) => {
    const updated = await api.renameConversation(id, title)
    setConversations((prev) => prev.map((c) => (c.id === id ? updated : c)))
  }

  const handleDelete = async (id: number) => {
    try {
      await api.deleteConversation(id)
      const rest = conversations.filter((c) => c.id !== id)
      setConversations(rest)
      if (id === currentId) {
        navigate(rest.length > 0 ? `/chat/${rest[0].id}` : '/chat', { replace: true })
      }
    } catch (e) {
      message.error(e instanceof Error ? e.message : '删除失败')
    }
  }

  const handleSend = async (content: string) => {
    if (!currentId) return
    setSending(true)
    setStreamingText('')

    // 乐观显示：先把用户这句话贴在界面上，不用等后端往返。
    // 负 id 只是 React 列表的 key，真实 id 在下次加载时由后端给出。
    const optimistic: MessageOut = {
      id: -Date.now(),
      role: 'user',
      content,
      status: 'completed',
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimistic])

    try {
      const reply = await api.sendMessage(currentId, content, (delta) =>
        setStreamingText((prev) => (prev ?? '') + delta),
      )
      setStreamingText(null)
      setMessages((prev) => [...prev, reply])
      // 后端的 last_message_at 变了，会话排序会变，刷新一下左侧列表
      await refreshConversations()
    } catch (e) {
      setStreamingText(null)
      // 注意：用户消息其实已经落库了（后端先存再调模型），所以这里不清掉它
      message.error(e instanceof Error ? e.message : '发送失败')
    } finally {
      setSending(false)
    }
  }

  return (
    <Layout style={{ height: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingInline: 20,
        }}
      >
        <Typography.Title level={4} style={{ color: '#fff', margin: 0 }}>
          Morrow · 超声检查知识助手
        </Typography.Title>
        <div>
          <Typography.Text style={{ color: 'rgba(255,255,255,0.75)', marginRight: 12 }}>
            {user?.nickname}
          </Typography.Text>
          <Button
            type="text"
            icon={<LogoutOutlined />}
            style={{ color: '#fff' }}
            onClick={() => {
              logout()
              navigate('/login', { replace: true })
            }}
          >
            退出
          </Button>
        </div>
      </Header>

      <Layout>
        <Sider width={280} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
          <ConversationList
            conversations={conversations}
            currentId={currentId}
            onSelect={(id) => navigate(`/chat/${id}`)}
            onCreate={handleCreate}
            onRename={handleRename}
            onDelete={handleDelete}
          />
        </Sider>

        <Content style={{ display: 'flex', flexDirection: 'column', background: '#fff' }}>
          {currentId ? (
            <>
              <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
                <MessageList
                  messages={messages}
                  loading={loadingMsgs}
                  streamingText={streamingText}
                />
              </div>
              <div style={{ borderTop: '1px solid #f0f0f0', padding: 16 }}>
                <MessageInput disabled={sending} onSend={handleSend} />
              </div>
            </>
          ) : (
            <Empty description="在左侧新建一个会话，然后开始提问" style={{ marginTop: 120 }} />
          )}
        </Content>
      </Layout>

      <Footer
        style={{
          textAlign: 'center',
          padding: '10px 0',
          background: '#fafafa',
          color: '#888',
          fontSize: 13,
        }}
      >
        本系统仅供健康科普与检查流程咨询，不替代医生诊断与治疗建议。
      </Footer>
    </Layout>
  )
}
