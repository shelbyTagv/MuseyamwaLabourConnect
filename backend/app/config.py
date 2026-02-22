"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/labourconnect"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@db:5432/labourconnect"

    # ── JWT / Auth ────────────────────────────────────────────
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Admin Seeding ─────────────────────────────────────────
    ADMIN_EMAIL: str = "admin@museyamwa.co.zw"
    ADMIN_PASSWORD: str = "Admin@12345"
    ADMIN_PHONE: str = "+263771234567"

    # ── Pesepay ───────────────────────────────────────────────
    PESEPAY_INTEGRATION_KEY: str = ""
    PESEPAY_ENCRYPTION_KEY: str = ""
    PESEPAY_API_URL: str = "https://api.pesepay.com/api/payments-engine/v2"
    PESEPAY_RETURN_URL: str = "http://localhost:3000/wallet"
    PESEPAY_RESULT_URL: str = "http://localhost:8000/api/v1/payments/webhook"

    # ── Application ───────────────────────────────────────────
    APP_NAME: str = "MuseyamwaLabourConnect"
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Token Economics ───────────────────────────────────────
    DEFAULT_TOKEN_PRICE_USD: float = 0.50
    TOKENS_PER_PURCHASE: int = 10
    JOB_POST_TOKEN_COST: int = 2
    JOB_REQUEST_TOKEN_COST: int = 1
    MESSAGE_TOKEN_COST: int = 1
    OFFER_TOKEN_COST: int = 1

    # ── GPS ───────────────────────────────────────────────────
    LOCATION_UPDATE_INTERVAL_SECONDS: int = 15
    MAX_PROXIMITY_KM: float = 50.0

    # ── Auto-seed (set to false once you have real data) ─────
    AUTO_SEED: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
