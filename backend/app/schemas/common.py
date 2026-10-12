from datetime import datetime, timezone
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, PlainSerializer

T = TypeVar("T")# T 是一个类型占位符


def _to_utc_iso(dt: datetime) -> str:
    """给库里存的 naive UTC 补上时区标记再输出。

    不补的话，浏览器会把 "2026-10-12T07:50:00" 当作**本地时间**解析，
    显示出来正好差一个时区（国内 8 小时）。
    """
    return dt.replace(tzinfo=timezone.utc).isoformat()


# 所有对外暴露的 datetime 字段都用它：库内是 naive UTC，出口补 +00:00。
# 用法见 schemas/user.py、schemas/conversation.py、schemas/message.py
UtcDatetime = Annotated[
    datetime,
    PlainSerializer(_to_utc_iso, return_type=str, when_used="json"),
]


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