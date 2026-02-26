import asyncio
import logging

from aiogram import Bot, Dispatcher
import certifi
from redis.asyncio import Redis

from config import load_settings
from handlers.bot_handlers import build_router
from storage.redis_repo import RedisRepo


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()

    redis = Redis.from_url(
        settings.redis_url,
        password=settings.redis_password or None,
        decode_responses=True,
        ssl_cert_reqs="required",
        ssl_ca_certs=certifi.where(),
    )

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    repo = RedisRepo(redis=redis, retention_hours=settings.retention_hours)
    dp.include_router(build_router(repo))

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
