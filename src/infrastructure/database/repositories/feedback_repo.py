"""
Репозиторий для vacancy_feedback.
Позволяет сохранять/обновлять реакцию пользователя на вакансию.
"""
import logging
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FeedbackRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_disliked_ids(self, user_id: UUID) -> list[str]:
        """Возвращает source_id всех вакансий, которые пользователь отметил 'dislike'."""
        stmt = text("""
            SELECT source_id FROM vacancy_feedback
            WHERE user_id = :user_id AND feedback = 'dislike'
        """)
        result = await self._session.execute(stmt, {"user_id": user_id})
        return [row[0] for row in result.fetchall()]

    async def upsert(
        self,
        user_id: UUID,
        source_id: str,
        feedback: str,
        source: str = "hh",
        vacancy_id: UUID | None = None,
    ) -> None:
        """
        Создаёт или обновляет запись фидбэка.
        Используем raw SQL через уникальный индекс (user_id, source_id, source).
        """
        now = datetime.utcnow()
        stmt = text("""
            INSERT INTO vacancy_feedback (id, user_id, vacancy_id, source_id, source, feedback, created_at)
            VALUES (:id, :user_id, :vacancy_id, :source_id, :source, :feedback, :created_at)
            ON CONFLICT (user_id, source_id, source)
            DO UPDATE SET feedback = EXCLUDED.feedback, created_at = EXCLUDED.created_at
        """)
        await self._session.execute(stmt, {
            "id": uuid4(),
            "user_id": user_id,
            "vacancy_id": vacancy_id,
            "source_id": source_id,
            "source": source,
            "feedback": feedback,
            "created_at": now,
        })
