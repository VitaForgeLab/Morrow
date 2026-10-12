# 个人信息最小化，暂不填手机邮箱
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column# Mapped 是 类型标注,mapped_column是定义这个数据表的列的参数
from app.database.base import Base, TimestampMixin

class User(TimestampMixin, Base):# 继承一些基本的属性
    __tablename__ = "user"  # 指定数据库里的表名

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,    # 自动带唯一索引，可以不用写 index=True
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )