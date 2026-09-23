from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession,async_sessionmaker
from ..core.config import settings

engine=create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping = True,# 取连接前探活，避免拿到的是断掉的连接
    pool_recycle = 3600, # 一小时回收
    pool_size = 5,
    max_overflow = 10,
    echo = True # 会打印SQL
)

AsyncSessionLocal = async_sessionmaker(
    bind = engine,
    class_= AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        # No commit operation here! Go to service/ to commit.

# 可以当模板复用，之后复用，顶多 pull size 或者 max overflow 改一改并发数，根据性能自己调一下
"""
pipline: 
路由函数→需要依赖get_db→开一个AsyncSessionLocal，去engine拿数据库连接
→拿完回来造一个session对话给get_db→等路由函数执行完之后，自动关掉session
"""