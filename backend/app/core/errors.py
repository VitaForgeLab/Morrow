# 模板级别代码，可复用（改改 logger 名字、改改 message 文案即可），不求完全会写
import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("morrow.error")
# 取一个名叫 morrow.error 的 logger
# 它继承了 main.py 里 logging.basicConfig(level=logging.INFO, ...) 的配置，所以 logger.exception(...) 会输出到终端

def register_exception_handlers(app: FastAPI) -> None:
    """把所有错误统一成 {code, message, data} 格式。"""

    """
    和 middleware.py的register_request_logging(app) 是一个套路：
    接收 FastAPI 应用对象。
    在函数内部用 @app.exception_handler(...) 把若干异常处理函数注册上去。
    注册后，一旦应用里抛出这些异常，FastAPI 就会调用对应的处理函数。
    """

    # ① 我们自己抛的 HTTPException（401 / 404 / 409 / 502 ...）（比如raise HTTPException(status_code=404, detail="用户不存在")），或者应用抛出的错误
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": str(exc.detail), "data": None},
            headers=exc.headers,      # 别丢：401 要靠它带 WWW-Authenticate
        )

    # ② 请求参数校验失败（Pydantic 在进端点之前就拦下了）
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,# 422表示请求格式对，但语义不合法，比如age:abc
            content={
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "请求参数校验失败",
                # jsonable_encoder 不能省，见下方坑 2
                "data": jsonable_encoder(exc.errors()),
            },
        )

    # ③ 兜底：任何没被处理的异常
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("未处理的异常: %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "服务器内部错误",
                "data": None,
            },
        )