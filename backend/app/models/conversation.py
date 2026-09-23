from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin

class Conversation(TimestampMixin, Base):
    __tablename__ = "conversation"  # 指定数据库里的表名

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.id"),
        nullable=False,
        # 这里不写 index=True：下面 __table_args__ 里的复合索引最左列就是 user_id，
        # 它本身就能用于“按 user_id 过滤”，再单独建一个索引是重复的。
    )
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="新对话"
    )
    last_message_at: Mapped[datetime] = mapped_column(  # 这个给聊天排序，而不是 created_at
        DateTime,
        nullable=False,
        # 同样不写 index=True：单独给 last_message_at 建索引没有意义
        # （你永远不会“跨所有用户按时间排会话”），它也加速不了下面那个主查询。
    )
    origin: Mapped[str] = mapped_column(  # 阶段三铺垫
        String(20),
        nullable=False,
        default="user"
    )

    __table_args__ = (
        # 会话列表的主查询：WHERE user_id = ? ORDER BY last_message_at DESC
        # 复合索引让“筛选 + 排序”一次走完；没有它，MySQL 只能先用 user_id
        # 筛出一堆行、再在内存里排序（filesort），会话一多就慢。
        # 不用写 DESC：MySQL 8 对 ASC 索引也能反向扫描来满足 DESC 排序。
        Index("ix_conversation_user_last_msg", "user_id", "last_message_at"),
    )# 暂时了解个大概