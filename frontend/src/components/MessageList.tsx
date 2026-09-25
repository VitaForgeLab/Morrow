import { useEffect, useRef } from 'react'
import { Empty, Spin, Tag } from 'antd'
import type { MessageOut, MessageRole, MessageStatus } from '../types/api.ts'
import Markdown from './Markdown.tsx'

interface Props {
  messages: MessageOut[]
  loading: boolean
  /** 正在生成中的文本（非 null 表示模型正在回答）。阶段 F 换 SSE 后这里会逐字增长 */
  streamingText: string | null
}

function Bubble({
  role,
  content,
  status,
}: {
  role: MessageRole
  content: string
  status: MessageStatus
}) {
  const isUser = role === 'user'

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 16,
      }}
    >
      <div style={{ maxWidth: '78%' }}>
        <div
          style={{
            fontSize: 12,
            color: '#999',
            marginBottom: 4,
            textAlign: isUser ? 'right' : 'left',
          }}
        >
          {isUser ? '我' : 'Morrow'}
          {status === 'streaming' && (
            <Tag color="processing" style={{ marginLeft: 8 }}>
              生成中
            </Tag>
          )}
          {status === 'failed' && (
            <Tag color="error" style={{ marginLeft: 8 }}>
              生成失败
            </Tag>
          )}
          {status === 'interrupted' && (
            <Tag color="warning" style={{ marginLeft: 8 }}>
              已中断
            </Tag>
          )}
        </div>

        <div
          style={{
            padding: '10px 14px',
            borderRadius: 8,
            background: isUser ? '#1677ff' : '#f5f5f5',
            color: isUser ? '#fff' : undefined,
            // 用户自己输入的是纯文本，保留换行即可；模型返回的是 Markdown，交给 Markdown 组件
            whiteSpace: isUser ? 'pre-wrap' : undefined,
            wordBreak: 'break-word',
          }}
        >
          {isUser ? content : <Markdown text={content} />}
        </div>
      </div>
    </div>
  )
}

export default function MessageList({ messages, loading, streamingText }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // 消息变化、或正在逐字生成时，自动滚到底部（对应 PRD 的 F13）
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', paddingTop: 60 }}>
        <Spin />
      </div>
    )
  }

  if (messages.length === 0 && streamingText === null) {
    return (
      <Empty
        description="还没有消息，在下面的输入框里问点什么吧"
        style={{ paddingTop: 100 }}
      />
    )
  }

  return (
    <div>
      {messages.map((m) => (
        <Bubble key={m.id} role={m.role} content={m.content} status={m.status} />
      ))}

      {/* 正在生成的那条：还没落库，先用一个临时气泡显示 */}
      {streamingText !== null && (
        <Bubble role="assistant" content={streamingText || '…'} status="streaming" />
      )}

      <div ref={bottomRef} />
    </div>
  )
}
