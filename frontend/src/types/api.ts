/**
 * 后端返回结构的 TypeScript 类型。
 *
 * 这里只写前端真正用到的字段 —— 和后端 schema 里的"白名单"思路一致：
 * 用不到的字段不写，将来后端加了新字段也不会悄悄影响前端。
 */

/** 统一响应信封（对应后端 app/schemas/common.py 的 ApiResponse） */
export interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
}

/** 用户信息（对应 UserOut） */
export interface UserOut {
  id: number
  username: string
  nickname: string
  created_at: string
}

/**
 * 注册 / 登录的返回值（对应 AuthResponse）。
 * 注意它【不是】信封：access_token 平铺在最外层，因为 Swagger 的
 * Authorize 按钮依赖这个结构（见 PRD §5.2 的例外说明）。
 */
export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserOut
}

/** 会话（对应 ConversationOut） */
export interface ConversationOut {
  id: number
  title: string
  last_message_at: string
  created_at: string
}

/** 消息角色。和后端 MessageRole 枚举一一对应 */
export type MessageRole = 'system' | 'user' | 'assistant'

/** 消息状态。status='streaming' 是阶段 F/G 做"切走不丢"时要用到的 */
export type MessageStatus = 'streaming' | 'completed' | 'failed' | 'interrupted'

/** 消息（对应 MessageOut） */
export interface MessageOut {
  id: number
  role: MessageRole
  content: string
  status: MessageStatus
  created_at: string
}
