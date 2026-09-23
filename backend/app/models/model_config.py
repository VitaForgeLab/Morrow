from sqlalchemy import JSON, BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin


class ModelConfig(TimestampMixin, Base):  # 类名改成大驼峰
    __tablename__ = "model_config"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="自己给模型取的别名，比如 deepseek-大肥鱼"
    )
    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="openai-compatible"
    )
    base_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    api_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="⚠️ 只存服务端配置，任何接口都不得下发前端"
    )
    model_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="真正发给 API 的 model 字段，如 deepseek-chat"
    )
    params: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="temperature / max_tokens 等参数"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否默认模型，应用层保证唯一"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    owner_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="NULL=系统配置；非空=用户自带（P2 BYOK）"
    )