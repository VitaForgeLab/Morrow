from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import UtcDatetime


class ConversationUpdate(BaseModel):
    """重命名请求体（PATCH 用）"""

    title: str = Field(min_length=1, max_length=100)


class ConversationOut(BaseModel):
    """会话的对外表示：只列前端真正需要的字段。"""

    model_config = ConfigDict(from_attributes=True)
    # from_attributes=True 允许从任意对象的属性（attribute）读取数据，而不是只从字典的键（key）读取
    # 比如service里面有：conv = await db.get(Conversation, 1)，返回的是ORM对象，不是字典

    id: int
    title: str
    last_message_at: UtcDatetime
    created_at: UtcDatetime

    # 故意不包含：
    #   user_id  —— 客户端已经知道自己是谁，返回它是冗余
    #   origin   —— 阶段三的内部字段，前端用不到