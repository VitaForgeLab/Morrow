from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """当前 UTC 时间（naive）。**全库时间基准的唯一来源。**

    为什么返回 naive（不带 tzinfo）而不是带时区的：
    MySQL 的 DATETIME 本身不存时区，把带 tzinfo 的时间传进去会被驱动**静默丢掉**。
    与其依赖这个隐式行为，不如显式约定——"库里存的一律是 UTC 墙钟时间"，
    出口处再由 API 补上时区标记（见 app/schemas/common.py 的 UtcDatetime）。
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


# 空白底座，赋予子类“成为数据库表”的能力。
# 放在 database/base.py 是为了防止循环导入，并划清基础设施层和业务层的界限。
class Base(DeclarativeBase):
    pass

# 抽 created_at / updated_at 到 base.py 复用
class TimestampMixin:#不继承任何class
    created_at:Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        # 由应用层生成 UTC。原来是 server_default=func.now()——那是数据库服务器的
        # 本地时间，会随部署机器的时区悄悄变化，且与 last_message_at 差 8 小时（见 B1）。
        # 代价：绕过 ORM 直接 INSERT 时必须自己提供这两个字段的值。
        default=utcnow)

    updated_at: Mapped[datetime] = mapped_column(
    DateTime, # 数据类型 时间
    nullable=False, # 不可为空
    default=utcnow,
    onupdate=utcnow # 👈 关键！每次 UPDATE 时自动刷新
)
"""
使用：
class User(TimestampMixin, Base):
    ...
Mixin在前
"""
# 基本就这样，不需要完全懂，也是一个模板