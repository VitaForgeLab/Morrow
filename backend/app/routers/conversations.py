from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.session import get_db
from app.models import Conversation, User, Message
from app.schemas.conversation import ConversationOut, ConversationUpdate
from app.services import conversation_service, message_service

from app.schemas.message import MessageOut

from app.schemas.message import ChatRequest, MessageOut
from app.services import chat_service, conversation_service, message_service



router = APIRouter(prefix="/conversations", tags=["会话"])

# ---------- 越权校验依赖（本阶段的核心）----------
async def get_owned_conversation(
    conversation_id: int,                                    # 路径参数，依赖也能声明
    current_user: User = Depends(get_current_user),           # 子依赖
    db: AsyncSession = Depends(get_db),                       # 子依赖
) -> Conversation:
    """确认会话存在【且属于当前用户】，否则 404。

    用 404 而不是 403：403 等于告诉对方"资源存在，只是不属于你"，
    等于泄露了资源存在性。404 什么都不说。
    """
    conv = await conversation_service.get_by_id(db, conversation_id)
    if conv is None or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conv

# ---------- 端点 ----------
@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """会话列表，按最近活跃倒序，分页。"""
    return await conversation_service.list_for_user(db, current_user.id, limit, offset)

@router.post("", response_model=ConversationOut)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """新建会话。不收请求体 —— 标题用默认的"新对话"，改名走 PATCH。"""
    return await conversation_service.create(db, current_user.id)


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(conv: Conversation = Depends(get_owned_conversation)):
    return conv


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def rename_conversation(
    data: ConversationUpdate,
    conv: Conversation = Depends(get_owned_conversation),
    db: AsyncSession = Depends(get_db),
):
    return await conversation_service.rename(db, conv, data.title)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conv: Conversation = Depends(get_owned_conversation),
    db: AsyncSession = Depends(get_db),
):
    """删除会话，消息由数据库级联一起删除。"""
    await conversation_service.delete(db, conv)
    return None

@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
# 获得某一个对话的所有 message
# 越权校验函数就在本文件，所以就不新建 service/message.py 了。
async def list_messages(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conv: Conversation = Depends(get_owned_conversation),
    db: AsyncSession = Depends(get_db),
):
    """会话的消息历史，按时间正序，分页。"""
    return await message_service.list_for_conversation(db, conv.id, limit, offset)

@router.post("/{conversation_id}/chat", response_model=MessageOut)
async def chat(
    data: ChatRequest,
    conv: Conversation = Depends(get_owned_conversation),
    db: AsyncSession = Depends(get_db),
):
    """发一条消息，同步等模型给出完整回答（暂时不做流式）。"""
    return await chat_service.reply(db, conv, data.content)