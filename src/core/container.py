from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.ai.claude_service import ClaudeAIService
from src.infrastructure.ai.rate_limiter import RedisRateLimiter
from src.infrastructure.database.repositories.application_repo import ApplicationRepositoryImpl
from src.infrastructure.database.repositories.user_repo import UserRepositoryImpl
from src.infrastructure.database.repositories.vacancy_repo import VacancyRepositoryImpl
from src.infrastructure.external.hh_client import HHClient


@dataclass
class Container:
    user_repo: UserRepositoryImpl
    vacancy_repo: VacancyRepositoryImpl
    application_repo: ApplicationRepositoryImpl
    ai_service: ClaudeAIService
    hh_client: HHClient
    rate_limiter: RedisRateLimiter = field(default_factory=RedisRateLimiter)


def create_container(session: AsyncSession) -> Container:
    return Container(
        user_repo=UserRepositoryImpl(session),
        vacancy_repo=VacancyRepositoryImpl(session),
        application_repo=ApplicationRepositoryImpl(session),
        ai_service=ClaudeAIService(),
        hh_client=HHClient(),
        rate_limiter=RedisRateLimiter(),
    )
