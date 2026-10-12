# 进程级的大模型客户端（与 database/session.py 里的 engine 同级的基础设施）。
#
# 为什么单独一个模块：OpenAI SDK 的客户端内部持有一份 httpx 连接池。
# 每次请求新建一个，就等于每次都重新握手 TLS、完全用不上 keep-alive（B2）。
# 所以把它做成"按配置缓存 + 应用退出时关闭"的进程级资源。
#
# 放 core/ 而不是 services/：它是基础设施，service 层只能依赖它，不能反过来。
from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None
_signature: tuple[str, str] | None = None  # (base_url, api_key)：配置变了就重建


async def get_client(api_key: str, base_url: str) -> AsyncOpenAI:
    """取当前配置对应的客户端，能复用就复用。"""
    global _client, _signature

    signature = (base_url, api_key)
    if _client is None or _signature != signature:
        await close_client()  # 配置变了：先关掉旧的，避免连接池泄漏
        _client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        _signature = signature
    return _client


async def close_client() -> None:
    """关闭客户端。由 lifespan 在应用退出时调用——否则 httpx 连接池不会被回收。"""
    global _client, _signature
    if _client is not None:
        await _client.close()
        _client = None
        _signature = None
