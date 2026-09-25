import { useState } from 'react'
import { Button, Input } from 'antd'

interface Props {
  disabled: boolean
  onSend: (content: string) => void
}

export default function MessageInput({ disabled, onSend }: Props) {
  const [value, setValue] = useState('')

  const submit = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
  }

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
      <Input.TextArea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="问点什么…（Enter 发送，Shift + Enter 换行）"
        autoSize={{ minRows: 1, maxRows: 6 }}
        maxLength={4000}
        disabled={disabled}
        onPressEnter={(e) => {
          // 单独按 Enter 发送，Shift+Enter 换行
          if (!e.shiftKey) {
            e.preventDefault()
            submit()
          }
        }}
      />
      <Button type="primary" onClick={submit} loading={disabled} style={{ height: 40 }}>
        发送
      </Button>
    </div>
  )
}
