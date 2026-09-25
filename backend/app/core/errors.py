# 暂时不看
import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("morrow.error")


def register_exception_handlers(app: FastAPI) -> None:
    """把所有错误统一成 {code, message, data} 格式。"""

    # ① 我们自己抛的 HTTPException（401 / 404 / 409 / 502 ...）
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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