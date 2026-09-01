from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Converza"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "converza-secret-super-key-2026-whatsapp-crm-brazil"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = "postgresql+psycopg://postgres@127.0.0.1:5432/converza_db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()