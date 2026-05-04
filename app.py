import logging
import os
from functools import lru_cache

import certifi
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from redis.asyncio import Redis

from config import Settings, load_settings
from handlers.bot_handlers import build_router
from storage.redis_repo import RedisRepo
from storage.upstash_rest import UpstashRestRedis


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@lru_cache(maxsize=1)
def _settings() -> Settings:
    return load_settings()


@lru_cache(maxsize=1)
def _webhook_secret() -> str:
    secret = os.getenv("WEBHOOK_SECRET", "").strip()
    if not secret:
        raise ValueError("WEBHOOK_SECRET is required for webhook mode")
    return secret


@lru_cache(maxsize=1)
def _bot() -> Bot:
    return Bot(token=_settings().bot_token)


@lru_cache(maxsize=1)
def _redis() -> Redis:
    rest_url = (
        os.getenv("KV_REST_API_URL", "").strip()
        or os.getenv("UPSTASH_REDIS_REST_API_URL", "").strip()
        or os.getenv("UPSTASH_REDIS_REST_URL", "").strip()
    )
    rest_token = (
        os.getenv("KV_REST_API_TOKEN", "").strip()
        or os.getenv("UPSTASH_REDIS_REST_API_TOKEN", "").strip()
        or os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    )
    if rest_url and rest_token:
        return UpstashRestRedis(rest_url=rest_url, rest_token=rest_token)

    settings = _settings()
    return Redis.from_url(
        settings.redis_url,
        password=settings.redis_password or None,
        decode_responses=True,
        ssl_cert_reqs="required",
        ssl_ca_certs=certifi.where(),
    )


@lru_cache(maxsize=1)
def _dispatcher() -> Dispatcher:
    settings = _settings()
    repo = RedisRepo(redis=_redis(), retention_hours=settings.retention_hours)
    dp = Dispatcher()
    dp.include_router(build_router(repo))
    return dp


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "mode": "webhook"}


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        await _redis().ping()
    except Exception as exc:  # noqa: BLE001
        logger.exception("redis_health_failed")
        raise HTTPException(status_code=503, detail=f"Redis error: {exc}") from exc
    return {"status": "ok", "redis": "ok", "mode": "webhook"}


@app.post("/webhook/{secret}")
async def telegram_webhook(
    secret: str,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    expected_secret = _webhook_secret()
    if secret != expected_secret or x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await request.json()
    update = Update.model_validate(data, context={"bot": _bot()})
    await _dispatcher().feed_update(_bot(), update)
    return {"ok": True}
