from datetime import datetime, timezone

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Message

DEFAULT_TITLE = "新对话"


async def get_empty_for_user(db: AsyncSession, user_id: int) -> Conversation | None:
    """找出该用户"还没问过话"的会话（一条消息都没有）。

    用 NOT EXISTS 子查询判断有没有消息，而不是拿 last_message_at 和 created_at 比 ——
    后者依赖"两个时间戳恰好相等"这个隐含约定，读起来也不直白。
    走的是 message 表上 (conversation_id, id) 那条索引。
    """
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.user_id == user_id,
            ~exists(
                select(Message.id).where(Message.conversation_id == Conversation.id)
            ),
        )
        .order_by(Conversation.id.desc())
        .limit(1)
    )
    return result.scalars().first()


async def create(db: AsyncSession, user_id: int, title: str | None = None) -> Conversation:
    """拿到一个"可以开始问话的会话"。

    如果该账号已经有一个还没问过话的会话，直接返回它、不再新建 ——
    否则用户可以反复点"新建会话"，堆出一长串空会话。
    """
    existing = await get_empty_for_user(db, user_id)
    if existing is not None:
        return existing

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