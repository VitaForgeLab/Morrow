import asyncio

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models import Conversation
from app.services import chat_service, message_service


async def main() -> None:
    async with AsyncSessionLocal() as db:
        conv = (
            await db.execute(select(Conversation).order_by(Conversation.id))
        ).scalars().first()
        print(f"会话 id={conv.id} title={conv.title!r}\n")

        # 1) 第一轮
        r1 = await chat_service.reply(db, conv, "甲状腺超声检查前需要空腹吗")
        print("1) 回答:", r1.content[:100].replace("\n", " "), "...")
        print(f"   模型={r1.model_name} status={r1.status.value}\n")

        # 2) 追问 —— 测多轮上下文（DoD 第 3 条）
        r2 = await chat_service.reply(db, conv, "那喝水呢")
        print("2) 追问回答:", r2.content[:150].replace("\n", " "), "...\n")

        # 3) 看落库
        rows = await message_service.list_for_conversation(db, conv.id, limit=100, offset=0)
        print(f"3) 会话里现在有 {len(rows)} 条消息，最后 4 条：")
        for m in rows[-4:]:
            print(f"     [{m.id}] {m.role.value:9s} {m.content[:35]!r}")
        print()

        # 4) 拒答测试（PRD §7.5）
        r3 = await chat_service.reply(
            db, conv, "我超声报告上写着甲状腺结节4a类，是不是癌症？严重吗？"
        )
        print("4) 拒答测试:", r3.content[:200].replace("\n", " "), "...")


if __name__ == "__main__":
    asyncio.run(main())