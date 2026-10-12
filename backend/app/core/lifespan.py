# 应用级资源的生命周期（FastAPI 的 lifespan 机制）
#
# 与 main.py 的关系：main.py 把 lifespan 传给 FastAPI 构造函数，
# 于是"启动前"和"退出后"各有一段代码可以跑。
#
# 这里只处理"退出"：大模型客户端是按需懒加载的（配置存在数据库里，
# 启动时不一定读得到），但必须在退出时关掉，否则 httpx 连接池不会被回收。
# 将来要在启动时预热什么（比如预读一次默认模型配置），也加在这里。
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import llm_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await llm_client.close_client()
