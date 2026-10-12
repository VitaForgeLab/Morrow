import logging

from fastapi import FastAPI

from app.api import api_router
from app.core.errors import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.middleware import register_request_logging

logging.basicConfig(
    level=logging.INFO,# 设置根 logger（root logger）的日志级别为 INFO，而处理优先级是DEBUG < INFO < WARNING < ERROR < CRITICAL，因此INFO以及以上级别的日志都会被处理并输出
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    # 一条日志大概这样：2025-01-01 12:00:00,123 INFO morrow.request | GET /api/users -> 200  12.3ms
)

app = FastAPI(title="Morrow", lifespan=lifespan)

register_exception_handlers(app)
register_request_logging(app)# 把实例给中间件日志打印函数，每一次请求都打印一下

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}