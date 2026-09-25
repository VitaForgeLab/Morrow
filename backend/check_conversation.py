import asyncio

from app.database.session import AsyncSessionLocal
from app.schemas.user import UserCreate
from app.services import conversation_service, user_service


async def main() -> None:
    async with AsyncSessionLocal() as db:
        # 借一个用户用；没有就现场建一个
        user = await user_service.get_by_username(db, "alice")
        if user is None:
            user = await user_service.register(
                db, UserCreate(username="alice", password="123456")
            )
        print(f"用户: id={user.id} username={user.username}")

        # 1) 建三个会话
        for _ in range(3):
            c = await conversation_service.create(db, user.id)
            print(f"1) 新建 id={c.id} title={c.title!r} last_message_at={c.last_message_at}")

        # 2) 列表：按最近活跃倒序
        rows = await conversation_service.list_for_user(db, user.id, limit=10, offset=0)
        print("2) 列表(倒序):", [c.id for c in rows])

        # 3) 改名
        renamed = await conversation_service.rename(db, rows[0], "甲状腺检查")
        print(f"3) 改名: id={renamed.id} title={renamed.title!r}")

        # 4) 分页
        page = await conversation_service.list_for_user(db, user.id, limit=2, offset=2)
        print("4) limit=2 offset=2 →", [c.id for c in page])

        # 5) 删除
        await conversation_service.delete(db, renamed)
        rest = await conversation_service.list_for_user(db, user.id, limit=10, offset=0)
        print("5) 删掉后剩:", [c.id for c in rest])


if __name__ == "__main__":
    asyncio.run(main())