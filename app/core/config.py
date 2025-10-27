from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: AnyUrl                    # e.g. postgresql+asyncpg://user:pass@localhost:5432/inkboard
    SECRET_KEY: str
    REDIS_URL: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    REFRESH_TOKEN_EXPIRE_DAYS: int 
    ALGORITHM: str 
    APP_NAME: str 
    APP_VERSION: str 


settings = Settings()