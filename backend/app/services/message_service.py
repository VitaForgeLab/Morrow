from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message


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