from datetime import date, datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis

from src.core.config import settings

# Лимиты по умолчанию (free tier)
DAILY_LIMITS: dict[str, int] = {
    "cover_letter": 3,
    "mock_interview": 1,
}


class RedisRateLimiter:
    def __init__(self) -> None:
        self._redis = aioredis.from_url(
            settings.redis.url,
            decode_responses=True,
        )

    def _key(self, user_id: UUID, action: str) -> str:
        today = date.today().isoformat()  # "2026-03-22"
        return f"rl:{user_id}:{action}:{today}"

    def _seconds_until_midnight(self) -> int:
        now = datetime.now(tz=timezone.utc)
        midnight = now.replace(hour=23, minute=59, second=59, microsecond=0)
        return max(1, int((midnight - now).total_seconds()))

    async def check(self, user_id: UUID, action: str) -> bool:
        """
        Возвращает True если лимит не превышен и инкрементирует счётчик.
        Возвращает False если лимит исчерпан.
        """
        limit = DAILY_LIMITS.get(action, 10)
        key = self._key(user_id, action)
        ttl = self._seconds_until_midnight()

        async with self._redis.pipeline(transaction=True) as pipe:
            await pipe.incr(key)
            await pipe.expire(key, ttl)
            results = await pipe.execute()

        current: int = results[0]
        return current <= limit

    async def get_remaining(self, user_id: UUID, action: str) -> int:
        """Возвращает оставшееся количество запросов на сегодня."""
        limit = DAILY_LIMITS.get(action, 10)
        key = self._key(user_id, action)
        raw = await self._redis.get(key)
        used = int(raw) if raw else 0
        return max(0, limit - used)

    async def close(self) -> None:
        await self._redis.aclose()
