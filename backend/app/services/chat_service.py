# 聊天业务的编排，结合conversation_service, llm_service, message_service
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.prompt import SYSTEM_PROMPT
from app.models import Conversation, Message, MessageRole, MessageStatus
from app.services import conversation_service, llm_service, message_service

# v1PRD §7.2：每次带上最近 N 条已完成的消息作为上下文
HISTORY_LIMIT = 10


async def reply(db: AsyncSession, conv: Conversation, user_content: str) -> Message:
    """完成一次问答。

    存用户消息 → 拼上下文 → 调模型 → 存回答 → 刷新会话活跃时间
    """
    # 1) 先落库用户消息（刻意放调模型之前，否则调模型失败了，你发的用户消息也会消失；下面取历史上下文的时候，会把刚存的这条用户消息也带进来）
    await message_service.create(
        db, conv.id, MessageRole.USER, user_content, MessageStatus.COMPLETED
    )

    # 2) 取最近 N 条已完成的消息（会包含刚存进去的那条）
    history = await message_service.list_recent_completed(db, conv.id, HISTORY_LIMIT)

    # 3) 拼上下文：system prompt + 历史（本轮用户消息已在历史末尾）
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m.role.value, "content": m.content} for m in history
    ]

    # 4) 调模型
    try:
        answer, model_name = await llm_service.complete(db, messages)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail="上游模型调用失败，请稍后重试"
        ) from exc

    # 5) 存回答
    assistant_msg = await message_service.create(
        db,
        conv.id,
        MessageRole.ASSISTANT,
        answer,
        MessageStatus.COMPLETED,
        model_name=model_name,
    )

    # 6) 刷新会话活跃时间（会话列表的排序依据）
    await conversation_service.touch_last_message_at(db, conv)

    return assistant_msg