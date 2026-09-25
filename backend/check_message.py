import asyncio

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models import Conversation, Message, MessageRole, MessageStatus
from app.services import message_service


async def main() -> None:
    async with AsyncSessionLocal() as db:
        conv = (
            await db.execute(select(Conversation).order_by(Conversation.id))
        ).scalars().first()
        if conv is None:
            print("库里没有会话 —— 先跑一次 check_conversation.py")
            return
        print(f"用会话 id={conv.id} title={conv.title!r}")

        # 造 5 条消息（chat 接口还没写，先直接插）
        for i in range(1, 6):
            db.add(
                Message(
                    conversation_id=conv.id,
                    role=MessageRole.USER if i % 2 else MessageRole.ASSISTANT,
                    content=f"第 {i} 条消息",
                    status=MessageStatus.COMPLETED,
                )
            )
        await db.commit()

        # 1) 正序全读
        rows = await message_service.list_for_conversation(db, conv.id, limit=10, offset=0)
        print("1) 正序:", [(m.id, m.role.value, m.content) for m in rows])

        # 2) 分页
        page = await message_service.list_for_conversation(db, conv.id, limit=2, offset=2)
        print("2) limit=2 offset=2 →", [(m.id, m.content) for m in page])


if __name__ == "__main__":
    asyncio.run(main())