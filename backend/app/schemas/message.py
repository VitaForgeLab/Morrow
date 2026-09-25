from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import MessageRole, MessageStatus


class MessageOut(BaseModel):
    """消息的对外表示。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: MessageRole
    content: str
    status: MessageStatus
    created_at: datetime

    # 故意不包含：
    #   conversation_id —— 路径里已经有会话 id 了，冗余
    #   model_name / error_message —— 排查用的，前端暂时不需要

class ChatRequest(BaseModel):
    """发消息的请求体。"""

    content: str = Field(min_length=1, max_length=4000)