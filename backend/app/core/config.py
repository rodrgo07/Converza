from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Converza"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "converza-secret-super-key-2026-whatsapp-crm-brazil"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = "postgresql+psycopg://converza:converza_secret_pass@localhost:5432/converza"
    
    # Meta / WhatsApp Cloud API Config
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "converza_verify_token_2026"
    WHATSAPP_API_VERSION: str = "v19.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()