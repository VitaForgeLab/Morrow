import { request } from './client.ts'
import type { ConversationOut, MessageOut } from '../types/api.ts'

/* ---------- 会话 ---------- */

export function listConversations(limit = 20, offset = 0): Promise<ConversationOut[]> {
  return request<ConversationOut[]>(`/conversations?limit=${limit}&offset=${offset}`)
}

/** 新建会话。后端不收请求体，标题用默认的"新对话" */
export function createConversation(): Promise<ConversationOut> {
  return request<ConversationOut>('/conversations', { method: 'POST' })
}

export function renameConversation(id: number, title: string): Promise<ConversationOut> {
  return request<ConversationOut>(`/conversations/${id}`, {
    method: 'PATCH',
    body: { title },
  })
}

export function deleteConversation(id: number): Promise<null> {
  return request<null>(`/conversations/${id}`, { method: 'DELETE' })
}

/* ---------- 消息 ---------- */

export function listMessages(id: number, limit = 100, offset = 0): Promise<MessageOut[]> {
  return request<MessageOut[]>(`/conversations/${id}/messages?limit=${limit}&offset=${offset}`)
}

/**
 * 发消息并拿到回答。
 *
 * ⚠️ 这个函数的签名是【按流式设计的】，但当前实现是非流式的：
 * 后端要等模型说完才一次性返回，所以 onDelta 只会在最后被调用一次。
 *
 * 阶段 F 上 SSE 时，只改这个函数的内部（换成 fetch + response.body.getReader()
 * 逐块解析），调用方一行都不用动 —— 这是刻意留的接口。
 */
export async function sendMessage(
  conversationId: number,
  content: string,
  onDelta: (text: string) => void,
): Promise<MessageOut> {
  const msg = await request<MessageOut>(`/conversations/${conversationId}/chat`, {
    method: 'POST',
    body: { content },
  })
  onDelta(msg.content)
  return msg
}
