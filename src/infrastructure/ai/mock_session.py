"""
Хранилище сессий mock-интервью в Redis.
Ключ: mock:{user_id}:{session_id}
TTL: 2 часа (сессия завершается автоматически).
"""
import json
import logging
from uuid import UUID, uuid4

import redis.asyncio as aioredis

from src.core.config import settings

logger = logging.getLogger(__name__)

SESSION_TTL = 7200   # 2 часа
MAX_QUESTIONS = 5


class MockSessionRepository:
    def __init__(self) -> None:
        self._redis = aioredis.from_url(settings.redis.url, decode_responses=True)

    def _key(self, user_id: UUID, session_id: str) -> str:
        return f"mock:{user_id}:{session_id}"

    async def create(
        self,
        user_id: UUID,
        vacancy_id: UUID,
        vacancy_title: str,
        company: str,
        description: str,
        requirements: str,
    ) -> str:
        """Создаёт новую сессию и возвращает session_id."""
        session_id = str(uuid4())
        data = {
            "vacancy_id": str(vacancy_id),
            "vacancy_title": vacancy_title,
            "company": company,
            "description": description,
            "requirements": requirements,
            "history": [],        # list of {question, answer}
            "question_num": 1,
            "current_question": "",
            "is_finished": False,
        }
        await self._redis.setex(
            self._key(user_id, session_id),
            SESSION_TTL,
            json.dumps(data, ensure_ascii=False),
        )
        return session_id

    async def get(self, user_id: UUID, session_id: str) -> dict | None:
        raw = await self._redis.get(self._key(user_id, session_id))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def save(self, user_id: UUID, session_id: str, data: dict) -> None:
        await self._redis.setex(
            self._key(user_id, session_id),
            SESSION_TTL,
            json.dumps(data, ensure_ascii=False),
        )

    async def delete(self, user_id: UUID, session_id: str) -> None:
        await self._redis.delete(self._key(user_id, session_id))

    async def close(self) -> None:
        await self._redis.aclose()
