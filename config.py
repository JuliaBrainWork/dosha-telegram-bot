import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    redis_url: str
    redis_password: str | None
    retention_hours: int


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")

    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        raise ValueError("REDIS_URL is required")

    redis_password = os.getenv("REDIS_PASSWORD")
    retention_hours_raw = os.getenv("RETENTION_HOURS", "24").strip()

    try:
        retention_hours = int(retention_hours_raw)
    except ValueError as exc:
        raise ValueError("RETENTION_HOURS must be integer") from exc

    if retention_hours < 1:
        raise ValueError("RETENTION_HOURS must be >= 1")

    return Settings(
        bot_token=bot_token,
        redis_url=redis_url,
        redis_password=redis_password,
        retention_hours=retention_hours,
    )
