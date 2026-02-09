from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):

    APP_NAME: Optional[str] = None
    APP_VERSION: str
    OPENAI_API_KEY: str

    FILE_ALLOWED_TYPES: list[str]
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: Optional[str] = None

    MONGODB_URL: str
    MONGODB_DB: str

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
