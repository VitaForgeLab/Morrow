# 聊天业务的编排，结合conversation_service, llm_service, message_service
import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.prompt import SYSTEM_PROMPT
from app.models import Conversation, Message, MessageRole, MessageStatus
from app.services import conversation_service, llm_service, message_service

logger = logging.getLogger("morrow.chat")

# v1PRD §7.2：每次带上最近 N 条已完成的消息作为上下文
HISTORY_LIMIT = 10

# message.error_message 是 VARCHAR(500)：截断时留一点余量，
# 否则超长会抛 DataError，让"记录失败"这件事本身也失败
ERROR_MESSAGE_MAX_LEN = 480


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
        # 1) 先记日志：带 traceback，保证即使下一步落库也失败，原因不会一起丢
        logger.exception("模型调用失败 conversation_id=%s", conv.id)

        # 2) 再把失败落库，让"失败"成为可见数据（v1PRD §4.3 的 status / error_message）
        await message_service.create(
            db,
            conv.id,
            MessageRole.ASSISTANT,
            "",  # 内容留空：让前端按 status 决定渲染什么，避免"内容"和"状态"两处表达同一件事
            MessageStatus.FAILED,
            error_message=str(exc)[:ERROR_MESSAGE_MAX_LEN],
        )

        # 3) 最后才抛：异常链照旧保留。
        #    这里异常来自网络调用，会话仍健康，所以不需要 rollback
        #    （若异常来自数据库操作本身，那个会话会进入失败事务状态，必须先 await db.rollback()）
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