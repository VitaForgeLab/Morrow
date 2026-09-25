from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")# T 是一个类型占位符


class ApiResponse(BaseModel, Generic[T]):
    """业务接口的统一响应信封。

    【不使用】它的接口（都是刻意例外）：
    - /auth/register、/auth/login —— 必须扁平返回 access_token，
      Swagger 的 Authorize 按钮依赖它
    - SSE 流式接口（阶段 F）—— 流式的，没法包
    - /health —— 基础设施探活，不是业务接口
    """

    code: int = 200
    message: str = "success"
    data: T | None = None