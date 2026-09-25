from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationUpdate(BaseModel):
    """重命名请求体（PATCH 用）"""

    title: str = Field(min_length=1, max_length=100)


class ConversationOut(BaseModel):
    """会话的对外表示：只列前端真正需要的字段。"""

    model_config = ConfigDict(from_attributes=True)# 暂时不懂

    id: int
    title: str
    last_message_at: datetime
    created_at: datetime

    # 故意不包含：
    #   user_id  —— 客户端已经知道自己是谁，返回它是冗余
    #   origin   —— 阶段三的内部字段，前端用不到