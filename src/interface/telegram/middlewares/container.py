from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.ai.claude_service import ClaudeAIService
from src.infrastructure.ai.mock_session import MockSessionRepository
from src.infrastructure.database.connection import AsyncSessionFactory
from src.infrastructure.database.repositories.application_repo import ApplicationRepositoryImpl
from src.infrastructure.database.repositories.feedback_repo import FeedbackRepositoryImpl
from src.infrastructure.database.repositories.user_repo import UserRepositoryImpl
from src.infrastructure.database.repositories.vacancy_repo import VacancyRepositoryImpl
from src.infrastructure.external.hh_client import HHClient
from src.infrastructure.external.superjob_client import SuperJobClient
from src.infrastructure.external.telegram_parser import TelegramChannelParser

if TYPE_CHECKING:
    from src.events.career_week.services.cache import CareerWeekCacheService
    from src.events.career_week.services.registration import CareerWeekRegistrationService
    from src.events.career_week.services.sheets import GoogleSheetsService


@dataclass
class Container:
    session: AsyncSession
    user_repo: UserRepositoryImpl
    vacancy_repo: VacancyRepositoryImpl
    application_repo: ApplicationRepositoryImpl
    feedback_repo: FeedbackRepositoryImpl
    ai_service: ClaudeAIService
    hh_client: HHClient
    superjob_client: SuperJobClient
    telegram_parser: TelegramChannelParser
    mock_session_repo: MockSessionRepository
    # Career Week (опциональные, None если CAREER_WEEK_ENABLED=False)
    cw_sheets: GoogleSheetsService | None = field(default=None)
    cw_cache: CareerWeekCacheService | None = field(default=None)
    cw_registration: CareerWeekRegistrationService | None = field(default=None)


class ContainerMiddleware(BaseMiddleware):
    """Собирает все зависимости и кладёт в data["container"]."""

    def __init__(
        self,
        cw_sheets: GoogleSheetsService | None = None,
        cw_cache: CareerWeekCacheService | None = None,
        cw_registration: CareerWeekRegistrationService | None = None,
    ) -> None:
        self._ai_service = ClaudeAIService()
        self._hh_client = HHClient()
        self._sj_client = SuperJobClient()
        self._tg_parser = TelegramChannelParser()
        self._mock_sessions = MockSessionRepository()
        self._cw_sheets = cw_sheets
        self._cw_cache = cw_cache
        self._cw_registration = cw_registration

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionFactory() as session:
            container = Container(
                session=session,
                user_repo=UserRepositoryImpl(session),
                vacancy_repo=VacancyRepositoryImpl(session),
                application_repo=ApplicationRepositoryImpl(session),
                feedback_repo=FeedbackRepositoryImpl(session),
                ai_service=self._ai_service,
                hh_client=self._hh_client,
                superjob_client=self._sj_client,
                telegram_parser=self._tg_parser,
                mock_session_repo=self._mock_sessions,
                cw_sheets=self._cw_sheets,
                cw_cache=self._cw_cache,
                cw_registration=self._cw_registration,
            )
            data["container"] = container
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
