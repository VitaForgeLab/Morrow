# 调大模型

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import llm_client
from app.services import model_config_service


async def complete(db: AsyncSession, messages: list[dict]) -> tuple[str, str]:
    """非流式调用大模型。

    返回 (回答文本, 使用的模型名)。
    """
    cfg = await model_config_service.get_default(db)
    if cfg is None:
        raise RuntimeError("没有可用的模型配置（model_config 表为空或没有默认项）")

    # 先把要用的值取成普通 Python 变量，再结束这次只读查询开启的事务。
    # 为什么要结束：这次 SELECT 会占住连接池里的一条连接，而下面那次网络调用可能
    # 持续 10–30 秒；事务不结束，连接就一直被占着，并发一上来先耗尽 pool_size（B10）。
    # 用 commit 而不是 rollback：sessionmaker 设了 expire_on_commit=False，
    # commit 不会让 ORM 对象过期，而下面的值已经取完、不再依赖会话。
    api_key = cfg.api_key
    base_url = cfg.base_url
    model_name = cfg.model_name
    params = dict(cfg.params or {})    # {"temperature":..., "max_tokens":...}
    await db.commit()

    # 客户端是进程级复用的（见 app/core/llm_client.py），不再每次请求新建
    client = await llm_client.get_client(api_key=api_key, base_url=base_url)
    resp = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        **params,# 字典解包，会把temperature= max_tokens=当参数传入
    )

    content = resp.choices[0].message.content or ""
    """
    返回的 resp 是一个 Pydantic 对象（OpenAI SDK 定义的）
    它对应的大概是这段 JSON:
    {
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1727241600,
  "model": "gpt-4o-mini-2024-07-18",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！有什么可以帮你的吗？"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 12,
    "total_tokens": 20
  }
}
    resp.choices[0].message.content 就是从这个结构里一层层往下取
    """
    return content, model_name