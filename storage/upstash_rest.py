from typing import Any

import aiohttp


class UpstashRestRedis:
    def __init__(self, rest_url: str, rest_token: str) -> None:
        self.rest_url = rest_url.rstrip("/")
        self.rest_token = rest_token

    async def _command(self, *parts: Any) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.rest_url}/pipeline",
                json=[[part for part in parts]],
                headers={"Authorization": f"Bearer {self.rest_token}"},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                payload = await response.json()

        item = payload[0]
        if "error" in item:
            raise RuntimeError(item["error"])
        return item.get("result")

    async def get(self, key: str) -> str | None:
        return await self._command("GET", key)

    async def set(self, key: str, value: str, *, ex: int | None = None) -> bool:
        if ex is None:
            result = await self._command("SET", key, value)
        else:
            result = await self._command("SET", key, value, "EX", ex)
        return result == "OK"

    async def delete(self, key: str) -> int:
        return int(await self._command("DEL", key))

    async def ping(self) -> bool:
        result = await self._command("PING")
        return result == "PONG"
