from pwdlib import PasswordHash

from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.models import User

# recommended() = 官方推荐的算法和参数（当前是 Argon2）
# 模块级只建一次：它内部会初始化哈希器，每次调用都重建是浪费
password_hash = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    """注册时用：把明文密码转成哈希串，存库"""
    return password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """登录时用：校验明文密码是否和库里的哈希匹配"""
    return password_hash.verify(plain, hashed)


# ---------- ↓JWT认证↓ ----------

# 从 Authorization: Bearer <token> 里抠出 <token>；没带这个头，直接 401。
# tokenUrl 只是给 /docs 的 Authorize 按钮看的，不创建任何接口。
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),                                   # JWT 规范里 sub 建议是字符串
        "exp": datetime.now(timezone.utc)                      # 什么时候失效
        + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),   # 子依赖：抠 token
    db: AsyncSession = Depends(get_db),    # 子依赖：查库
) -> User:
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录已失效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 把"这个 token 不可用"的所有情况收进同一个 try，统一转成 401
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise invalid

    user = await db.get(User, user_id)
    if user is None:
        raise invalid
    return user

# 多少有点难理解了😠回头治你