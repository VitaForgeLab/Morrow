"""__init__.py控制向外暴露的东西"""
"""
让外部可以少写一层路径，原来需要from app.models.conversation import Conversation,
但现在可以from app.models import Conversation
"""
from .conversation import Conversation #. 表示当前包，也就是 app.models
from .message import Message, MessageRole, MessageStatus
from .model_config import ModelConfig
from .user import User

__all__ = [
    "User",
    "Conversation",
    "Message",
    "ModelConfig",
    "MessageRole",
    "MessageStatus",
]