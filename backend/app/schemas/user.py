from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """注册请求体。这里是【请求】模型，和下面的UserOut【响应】模型不是一回事。"""

    username: str = Field(min_length=3, max_length=50)# Field是输入的请求体校验，你可以设置默认值、是否必填、最小最大长度等
    password: str = Field(min_length=6, max_length=128)

    # 没有 nickname：PRD §4.1 说"默认同 username"，由 service 层填
    # 没有邮箱 / 手机号：个人信息最小化（PRD §4.1、§7.5）


class UserOut(BaseModel):
    """用户信息的【对外表示】。只列能公开的字段"""

    model_config = ConfigDict(from_attributes=True)# 暂不理解

    id: int
    username: str
    nickname: str
    created_at: datetime


class Token(BaseModel):
    """OAuth2 标准要求的最外层字段，必须平铺，不能套进 data 里。"""

    access_token: str
    token_type: str = "bearer"


class AuthResponse(Token):
    """注册 / 登录的返回值：token 平铺 + 用户信息（PRD §5）。"""

    user: UserOut

# 以上就是请求体和响应模型的知识点，做好数据脱敏，不干涉业务，大概懂即可