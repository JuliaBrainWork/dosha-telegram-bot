import json
from datetime import datetime, timedelta, timezone
from typing import Any

from redis.asyncio import Redis


class RedisRepo:
    def __init__(self, redis: Redis, retention_hours: int) -> None:
        self.redis = redis
        self.retention_hours = retention_hours

    def _key(self, user_id: int) -> str:
        return f"dosha_test:session:{user_id}"

    async def get_session(self, user_id: int) -> dict[str, Any] | None:
        raw = await self.redis.get(self._key(user_id))
        if not raw:
            return None
        return json.loads(raw)

    async def save_session(self, user_id: int, session: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=self.retention_hours)
        session["updated_at"] = now.isoformat()
        session["ttl_expires_at"] = expires.isoformat()

        ttl_seconds = int(timedelta(hours=self.retention_hours).total_seconds())
        await self.redis.set(self._key(user_id), json.dumps(session, ensure_ascii=False), ex=ttl_seconds)

    async def delete_session(self, user_id: int) -> None:
        await self.redis.delete(self._key(user_id))

    async def create_new_session(self, user_id: int) -> dict[str, Any]:
        session = {
            "user_id": user_id,
            "current_mode": "prakriti",
            "current_index": 0,
            "answers": {"prakriti": {}, "vikriti": {}},
            "updated_at": "",
            "ttl_expires_at": "",
        }
        await self.save_session(user_id, session)
        return session
