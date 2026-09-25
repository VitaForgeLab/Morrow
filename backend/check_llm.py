import asyncio

from app.database.session import AsyncSessionLocal
from app.services import llm_service, model_config_service


async def main() -> None:
    async with AsyncSessionLocal() as db:
        cfg = await model_config_service.get_default(db)
        if cfg is None:
            print("model_config 里没有默认配置 —— 先执行上面那条 INSERT")
            return
        print(f"配置: name={cfg.name}")
        print(f"      base_url={cfg.base_url}")
        print(f"      model_name={cfg.model_name}")
        print(f"      params={cfg.params}")
        print(f"      api_key 前 8 位={cfg.api_key[:8]}...")

        content, model_name = await llm_service.complete(
            db, [{"role": "user", "content": "用一句话解释超声检查是什么"}]
        )
        print(f"\n回答（{model_name}）:\n{content}")


if __name__ == "__main__":
    asyncio.run(main())