from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password# 密码转哈希/密码和哈希值verify
from app.models import User# User的ORM模型
from app.schemas.user import UserCreate# 注册请求体模型


# 根据用户名查用户，查到返回 User 对象，查不到返回 None
async def get_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

# 主键查询用户
async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    # 主键查询，session.get() 是最短路径（还会先查身份映射，命中就不发 SQL）
    return await db.get(User, user_id)

async def register(db: AsyncSession, data: UserCreate) -> User:
    """注册。用户名重复抛 409。"""
    # 第一道：先查一次，为了给出友好提示
    if await get_by_username(db, data.username) is not None:
        raise HTTPException(status_code=409, detail="用户名已存在")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.username,          # v1PRD §4.1：默认同 username
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        # 第二道：并发窗口的兜底，同时add同一user必有一个IntegrityError
        await db.rollback()
        raise HTTPException(status_code=409, detail="用户名已存在")

    # 必须 refresh：把数据库生成的 id / created_at / updated_at 取回来
    await db.refresh(user)# id created_at这段是数据库生成的，提交后需要从数据库读回来，再一并发给客户端
    return user

# 登录时校验账号密码
async def authenticate(db: AsyncSession, username: str, password: str) -> User | None:
    """校验账号密码。任何一步失败都返回 None。"""
    user = await get_by_username(db, username)
    if user is None:# 防止已知用户被攻击
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

"""
路由层 router
  ↓ 接收 UserCreate、调用 service
Service 层（就是这段代码）
  ↓ 使用 AsyncSession 操作数据库
ORM 模型 User / 数据库表
"""