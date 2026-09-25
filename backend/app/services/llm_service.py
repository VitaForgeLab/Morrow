# 调大模型

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import model_config_service


async def complete(db: AsyncSession, messages: list[dict]) -> tuple[str, str]:
    """非流式调用大模型。

    返回 (回答文本, 使用的模型名)。
    """
    cfg = await model_config_service.get_default(db)
    if cfg is None:
        raise RuntimeError("没有可用的模型配置（model_config 表为空或没有默认项）")

    params = cfg.params or {}          # {"temperature":..., "max_tokens":...}

    # async with：用完自动关闭客户端（内部持有 httpx 连接池）,应该复用单个客户端，否则流量高性能受不了
    async with AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.base_url) as client:
        resp = await client.chat.completions.create(
            model=cfg.model_name,
            messages=messages,
            **params,
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
    return content, cfg.model_name