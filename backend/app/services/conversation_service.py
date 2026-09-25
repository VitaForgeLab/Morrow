from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation

DEFAULT_TITLE = "新对话"


async def create(db: AsyncSession, user_id: int, title: str | None = None) -> Conversation:
    now = datetime.now(timezone.utc)
    conv = Conversation(
        user_id=user_id,
        title=title or DEFAULT_TITLE,
        last_message_at=now,          # NOT NULL，且是列表排序依据，最新有消息的会话排最上面
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def list_for_user(
    db: AsyncSession, user_id: int, limit: int, offset: int
) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(
            Conversation.last_message_at.desc(),
            Conversation.id.desc(),          # 兜底，万一时间戳一样就看id
        )
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, conversation_id: int) -> Conversation | None:
    return await db.get(Conversation, conversation_id)# get方法，按主键查询


async def rename(db: AsyncSession, conv: Conversation, title: str) -> Conversation:
    conv.title = title
    await db.commit()
    await db.refresh(conv)
    return conv


async def delete(db: AsyncSession, conv: Conversation) -> None:
    # message 由数据库外键的 ON DELETE CASCADE 一起删，这里不用管
    await db.delete(conv)
    await db.commit()

async def touch_last_message_at(db: AsyncSession, conv: Conversation) -> None:
    """发消息后刷新活跃时间，让这个会话排到列表最前面。"""
    conv.last_message_at = datetime.now(timezone.utc)
    await db.commit()