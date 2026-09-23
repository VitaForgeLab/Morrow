# 建表脚本
import asyncio

from app import models
from app.database.base import Base
from app.database.session import engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("建表完成")


if __name__ == "__main__":
    asyncio.run(main())

"""
“如果这个脚本跑完，数据库里没建出表，可能是什么原因？”
答案：app/models/__init__.py 没导入模型，或者跑错目录导致 app 包路径不对，或者数据库连接配置错了。
"""