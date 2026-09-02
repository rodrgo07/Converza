from pydantic_settings import BaseSettings
from typing import Optional
import secrets
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Converza"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = ""
    
    # Meta / WhatsApp Cloud API Config
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_API_VERSION: str = "v19.0"
    WHATSAPP_APP_SECRET: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

if not settings.SECRET_KEY:
    settings.SECRET_KEY = secrets.token_hex(32)

if not settings.WHATSAPP_VERIFY_TOKEN:
    settings.WHATSAPP_VERIFY_TOKEN = "converza_verify_token_2026"

if not settings.DATABASE_URL:
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "converza.db")
    settings.DATABASE_URL = f"sqlite:///{db_path}"