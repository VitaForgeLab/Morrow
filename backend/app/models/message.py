from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column
# from ..database.base import TimestampMixin,Base
from app.database.base import TimestampMixin,Base

from enum import Enum
from sqlalchemy import Enum as SQLEnum  # ⚠️ 和 Python 的 Enum 重名，要起别名
class MessageRole(str, Enum):  # 继承 str 让它更好序列化
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
class MessageStatus(str, Enum):
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"




class Message(TimestampMixin,Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversation.id", ondelete="CASCADE"),  # ✅ CASCADE
        nullable=False,
        index=True  # ✅ 小写 index
    )
    role: Mapped[MessageRole] = mapped_column(
        # values_callable：强制落库用枚举的【值】（小写 system / user / assistant）。
        # 不加这个参数，SQLAlchemy 默认存的是【成员名】（大写 SYSTEM），
        # 就和 v1_prd.md §4.3 的 ENUM('system','user','assistant') 对不上了。
        SQLEnum(
            MessageRole,
            name="message_role_enum",
            values_callable=lambda cls: [m.value for m in cls],
        ),
        nullable=False,
    )
    status: Mapped[MessageStatus] = mapped_column(
        SQLEnum(
            MessageStatus,
            name="message_status_enum",
            values_callable=lambda cls: [m.value for m in cls],
        ),
        nullable=False,
        default=MessageStatus.STREAMING,
    )
    content: Mapped[str] = mapped_column(
        # 用 MEDIUMTEXT(16MB) 而不是 Text：MySQL 的 TEXT 只有 64KB（约 2 万汉字），
        # 长回答有溢出风险。PRD §4.3 指定的就是 MEDIUMTEXT。
        MEDIUMTEXT,
        nullable=False,
        # Python 侧默认值，正好避开 MySQL“TEXT 列不能有字面量默认值”的限制
        default="",
    )
    model_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )