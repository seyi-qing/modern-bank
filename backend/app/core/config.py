"""
Modern Bank - Core Configuration
================================
Centralized settings using Pydantic Settings.
In production, load from environment variables / secrets manager.
Never hardcode secrets in real banking systems.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ModernBank API"
    APP_VERSION: str = "1.3.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Security - CHANGE THESE IN PRODUCTION
    SECRET_KEY: str = "modern-bank-super-secret-key-change-me-in-prod-32chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database - SQLite for easy local demo.
    DATABASE_URL: str = "sqlite:///./modern_bank.db"

    # CORS - in production restrict to your frontend domain
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]

    DEFAULT_CURRENCY: str = "USD"
    MAX_TRANSFER_AMOUNT: float = 50000.0
    FRAUD_VELOCITY_THRESHOLD: int = 5
    MIN_PASSWORD_LENGTH: int = 8

    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    ENABLE_LIVE_PAYMENTS: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
