# connect to .env
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256" # 哈希算法
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7 # 7天过期


settings = Settings()