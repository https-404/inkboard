from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # Database
    DATABASE_URL: AnyUrl                    # e.g. postgresql+asyncpg://user:pass@localhost:5432/inkboard
    
    # Auth
    SECRET_KEY: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    REFRESH_TOKEN_EXPIRE_DAYS: int 
    ALGORITHM: str 

    # App
    APP_NAME: str 
    APP_VERSION: str 

    #Minio
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str
    MINIO_SECURE: bool = False


settings = Settings()