from pydantic import BaseModel, ConfigDict, Field

from app.models import MessageRole, MessageStatus
from app.schemas.common import UtcDatetime


class MessageOut(BaseModel):
    """消息的对外表示。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: MessageRole
    content: str
    status: MessageStatus
    created_at: UtcDatetime

    # 故意不包含：
    #   conversation_id —— 路径里已经有会话 id 了，冗余
    #   model_name / error_message —— 排查用的，前端暂时不需要

class ChatRequest(BaseModel):
    """发消息的请求体。"""

    content: str = Field(min_length=1, max_length=4000)
    """
    用户发消息时，只需要提供 content。
    role、status、conversation_id 这些都不该由客户端提供。
    role 由后端决定（用户消息是 user）。
    status 由后端决定（先 streaming，完成变 completed）。
    conversation_id 在 URL 路径里，不在 body 里。
    """