from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from sqlalchemy import DateTime, func

# 空白底座，赋予子类“成为数据库表”的能力。
# 放在 database/base.py 是为了防止循环导入，并划清基础设施层和业务层的界限。
class Base(DeclarativeBase):
    pass

# 抽 created_at / updated_at 到 base.py 复用
class TimestampMixin:#不继承任何class
    created_at:Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
    DateTime, # 数据类型 时间
    nullable=False, # 不可为空
    server_default=func.now(),# Mysql自己获取时间
    onupdate=func.now() # 👈 关键！每次 UPDATE 时自动刷新
)
"""
使用：
class User(TimestampMixin, Base):
    ...
Mixin在前
"""
# 基本就这样，不需要完全懂，也是一个模板