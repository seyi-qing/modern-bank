"""
Modern Bank - Core Configuration
================================
Centralized settings using Pydantic Settings.
In production, load from environment variables / secrets manager.
Never hardcode secrets in real banking systems.
"""

from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Union
import json


class Settings(BaseSettings):
    APP_NAME: str = "ModernBank API"
    APP_VERSION: str = "1.4.1"
    # Safe default: production must opt into debug explicitly.
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Kept for local SQLite development only. Production must provide SECRET_KEY.
    SECRET_KEY: str = "modern-bank-local-development-only-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./modern_bank.db"

    # Comma-separated or JSON list via env CORS_ORIGINS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "https://modern-bank-silk.vercel.app",
    ]

    DEFAULT_CURRENCY: str = "USD"
    MAX_TRANSFER_AMOUNT: float = 50000.0
    FRAUD_VELOCITY_THRESHOLD: int = 5
    MIN_PASSWORD_LENGTH: int = 8

    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    ENABLE_LIVE_PAYMENTS: bool = False

    @model_validator(mode="after")
    def validate_production_security(self):
        is_local_sqlite = self.DATABASE_URL.startswith("sqlite")
        if not is_local_sqlite and self.SECRET_KEY == "modern-bank-local-development-only-change-me":
            raise ValueError("SECRET_KEY must be explicitly configured for non-SQLite deployments")
        if not is_local_sqlite and self.DEBUG:
            raise ValueError("DEBUG must be false for non-SQLite deployments")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True

    def cors_list(self) -> List[str]:
        v = self.CORS_ORIGINS
        if isinstance(v, list):
            return v
        s = (v or "").strip()
        if not s:
            return []
        if s.startswith("["):
            try:
                return list(json.loads(s))
            except Exception:
                pass
        return [x.strip() for x in s.split(",") if x.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
