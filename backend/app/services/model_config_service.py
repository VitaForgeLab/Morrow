# 读大模型配置,不写入环境变量，而是从表读

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ModelConfig


async def get_default(db: AsyncSession) -> ModelConfig | None:
    """取当前生效的默认模型配置。"""
    result = await db.execute(
        select(ModelConfig).where(
            ModelConfig.is_default.is_(True),
            ModelConfig.is_active.is_(True),
        )
    )
    return result.scalars().first()