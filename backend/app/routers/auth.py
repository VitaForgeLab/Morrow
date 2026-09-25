from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.user import AuthResponse, UserCreate, UserOut
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=AuthResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """注册。成功直接返回 token —— 这就是 Todo 第 1 条的"注册后自动登录"。"""
    user = await user_service.register(db, data)
    return AuthResponse(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),   # ← 收【表单】，不是 JSON
    db: AsyncSession = Depends(get_db),
):
    """登录。字段名必须是 username / password，且以表单发送。"""
    user = await user_service.authenticate(db, form.username, form.password)
    if user is None:
        # 用户不存在和密码错误返回【完全相同】的响应，不给枚举用户名的机会
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthResponse(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)# UserOut保护了输出，所以即便 return current_user 也不会泄露密码
async def read_me(current_user: User = Depends(get_current_user)):
    """必须带 Authorization: Bearer <token> 才能访问。"""
    return current_user

"""
路由层算是好理解的，几个要点就是：
1. 注册时传入的是 JSON
2. 登录时传入的是表单
3. 获取当前用户时传入的是请求头 Bearer Token
4. 登录失败不要区分“用户不存在”和“密码错误”
"""