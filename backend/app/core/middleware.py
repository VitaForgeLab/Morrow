"""给 FastAPI 应用注册一个 HTTP 请求日志中间件，计时对流式响应不准"""
import logging
import time

from fastapi import FastAPI, Request

# 获取名为 morrow.request 的 logger
logger = logging.getLogger("morrow.request")


def register_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):# request 是 当前这次 HTTP 请求的对象。call_next是一个由框架传进来的回调函数，把请求继续交给后面的中间件和路由处理
        start = time.perf_counter()
        response = await call_next(request)# 等后面的中间件/路由处理结果并赋值给response
        cost_ms = (time.perf_counter() - start) * 1000# 乘1000，把默认的秒s转成毫秒ms
        logger.info(
            "%s %s -> %d  %.1fms",# 控制输出格式，如GET /api/users -> 200  12.3ms
            request.method,# 取请求方法，如GET、POST 等
            request.url.path,# 取请求路径，如/api/user
            response.status_code,
            cost_ms,
        )
        return response

# 全局且与业务无关的放中间件；需要知道"当前是哪个用户"的，比如认证，放依赖