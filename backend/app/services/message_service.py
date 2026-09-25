from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message, MessageRole, MessageStatus


async def list_for_conversation(
    db: AsyncSession, conversation_id: int, limit: int, offset: int
) -> list[Message]:
    """按会话取消息，按 id 正序，分页。"""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    conversation_id: int,
    role: MessageRole,
    content: str,
    status: MessageStatus,
    model_name: str | None = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        status=status,
        model_name=model_name,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def list_recent_completed(# 给大模型构造上下文，谁能看到？先 order by 加上 limit 列出最近的消息，最后再 reverse 输出给大模型（算是OpenAI的Message参数要求吧）
    db: AsyncSession, conversation_id: int, limit: int
) -> list[Message]:
    """取最近 N 条【已完成】的消息，按时间正序返回。"""
    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.status == MessageStatus.COMPLETED,
        )
        .order_by(Message.id.desc())
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))