# connect to .env
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # 会直接找工作目录下的.env，现在是backend。也可以BASE_DIR = Path(__file__).resolve().parent.parent，env_path = BASE_DIR / ".env"

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256" # 哈希算法
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7 # 7天过期
    SQL_ECHO: bool = False # 是否把每条 SQL 打到日志（排查时在 .env 里开，默认关）


settings = Settings()