from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DATABASE_URL: str = ""

    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""
    PAYSTACK_MIN_AMOUNT_KOBO: int = 3_500_000
    PAYSTACK_MAX_AMOUNT_KOBO: int = 3_700_000

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CLASSROOM_CHAT_ID: int = -1004498169669
    TELEGRAM_DISCUSSION_CHAT_ID: int = -1004365675295
    TELEGRAM_WEBHOOK_SECRET: str = ""

    ALLOWED_ORIGINS: str = "http://localhost:8000"
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    SUPPORT_WHATSAPP: str = "https://wa.me/2347068795736"

    ACCESS_DURATION_DAYS: int = 365
    INVITE_LINK_EXPIRE_HOURS: int = 48

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
