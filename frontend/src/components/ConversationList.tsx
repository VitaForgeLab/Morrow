import { useState } from 'react'
import { Button, Input, Modal, Popconfirm, Typography, message } from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import type { ConversationOut } from '../types/api.ts'

interface Props {
  conversations: ConversationOut[]
  currentId: number | null
  onSelect: (id: number) => void
  onCreate: () => void
  onRename: (id: number, title: string) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

/** 左侧会话列表（对应 PRD 的 F12 / F14）。
 *
 *  这里没有用 AntD 的 List —— 它在 AntD 6 已被标记废弃（官方建议换 Listy）。
 *  会话列表本身就是一个十几行的简单列表，用 div 直接渲染更稳，也少一个会被移除的依赖。 */
export default function ConversationList({
  conversations,
  currentId,
  onSelect,
  onCreate,
  onRename,
  onDelete,
}: Props) {
  const [editing, setEditing] = useState<ConversationOut | null>(null)
  const [draft, setDraft] = useState('')

  const submitRename = async () => {
    const title = draft.trim()
    if (!editing || !title) return
    try {
      await onRename(editing.id, title)
      setEditing(null)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '重命名失败')
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: 12 }}>
        <Button type="primary" block icon={<PlusOutlined />} onClick={onCreate}>
          新建会话
        </Button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {conversations.length === 0 && (
          <div style={{ padding: 16, color: '#999', textAlign: 'center', fontSize: 13 }}>
            还没有会话
          </div>
        )}

        {conversations.map((item) => (
          <div
            key={item.id}
            className="conv-item"
            onClick={() => onSelect(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 12px',
              cursor: 'pointer',
              background: item.id === currentId ? '#e6f4ff' : undefined,
            }}
          >
            <Typography.Text ellipsis style={{ flex: 1, minWidth: 0 }}>
              {item.title}
            </Typography.Text>

            <EditOutlined
              style={{ color: '#999' }}
              onClick={(e) => {
                // 阻止冒泡，否则会连带触发整行的"切换会话"
                e.stopPropagation()
                setEditing(item)
                setDraft(item.title)
              }}
            />

            <Popconfirm
              title="删除这个会话？"
              description="它下面的消息会一起删除。"
              okText="删除"
              cancelText="取消"
              onConfirm={() => onDelete(item.id)}
            >
              <DeleteOutlined
                style={{ color: '#999' }}
                onClick={(e) => e.stopPropagation()}
              />
            </Popconfirm>
          </div>
        ))}
      </div>

      <Modal
        open={editing !== null}
        title="重命名会话"
        okText="保存"
        cancelText="取消"
        onOk={submitRename}
        onCancel={() => setEditing(null)}
      >
        <Input
          value={draft}
          maxLength={100}
          onChange={(e) => setDraft(e.target.value)}
          onPressEnter={submitRename}
        />
      </Modal>
    </div>
  )
}
