from datetime import datetime
from uuid import UUID

from src.domain.entities.application import Application
from src.domain.entities.vacancy import Vacancy
from src.domain.repositories.application_repo import ApplicationRepository
from src.domain.repositories.vacancy_repo import VacancyRepository
from src.domain.value_objects.application_stage import ApplicationStage
from src.domain.value_objects.vacancy_source import VacancySource
from src.domain.value_objects.work_format import WorkFormat


class AddManualVacancy:
    """Добавляет вакансию вручную и сразу создаёт отклик со статусом SAVED."""

    def __init__(
        self,
        vacancy_repo: VacancyRepository,
        application_repo: ApplicationRepository,
    ) -> None:
        self._vacancy_repo = vacancy_repo
        self._application_repo = application_repo

    async def execute(
        self,
        user_id: UUID,
        title: str,
        company: str,
        url: str = "",
        notes: str = "",
    ) -> Application:
        vacancy = Vacancy(
            title=title,
            company=company,
            source=VacancySource.MANUAL,
            source_url=url,
        )
        vacancy = await self._vacancy_repo.create(vacancy)

        application = Application(
            user_id=user_id,
            vacancy_id=vacancy.id,
            stage=ApplicationStage.SAVED,
            notes=notes,
        )
        return await self._application_repo.create(application)


class SearchHHVacancies:
    """Ищет стажировки на hh.ru через внешний клиент."""

    def __init__(self, hh_client: object) -> None:
        self._hh_client = hh_client

    async def execute(
        self,
        query: str,
        city: str = "",
        work_format: WorkFormat | None = None,
        page: int = 0,
        per_page: int = 20,
    ) -> list[Vacancy]:
        filters: dict[str, object] = {
            "text": query,
            "page": page,
            "per_page": per_page,
        }
        if city:
            filters["area"] = city
        if work_format:
            filters["schedule"] = str(work_format)

        return await self._hh_client.search_vacancies(filters)  # type: ignore[attr-defined]


class AddVacancyFromURL:
    """Парсит вакансию по URL (hh.ru или другой источник) и создаёт отклик."""

    def __init__(
        self,
        hh_client: object,
        vacancy_repo: VacancyRepository,
        application_repo: ApplicationRepository,
    ) -> None:
        self._hh_client = hh_client
        self._vacancy_repo = vacancy_repo
        self._application_repo = application_repo

    async def execute(self, user_id: UUID, url: str) -> Application:
        # Проверяем — вдруг уже парсили эту вакансию
        source_id = self._extract_source_id(url)
        source = self._detect_source(url)

        existing = await self._vacancy_repo.get_by_source_id(source, source_id)
        if existing:
            vacancy = existing
        else:
            parsed: Vacancy = await self._hh_client.fetch_vacancy_by_url(url)  # type: ignore[attr-defined]
            parsed.source = source
            parsed.source_id = source_id
            parsed.source_url = url
            parsed.published_at = datetime.utcnow()
            vacancy = await self._vacancy_repo.create(parsed)

        # Проверяем — вдруг пользователь уже добавил эту вакансию
        existing_app = await self._application_repo.get_by_user_and_vacancy(
            user_id, vacancy.id
        )
        if existing_app:
            return existing_app

        application = Application(
            user_id=user_id,
            vacancy_id=vacancy.id,
            stage=ApplicationStage.SAVED,
        )
        return await self._application_repo.create(application)

    @staticmethod
    def _detect_source(url: str) -> VacancySource:
        if "hh.ru" in url or "headhunter.ru" in url:
            return VacancySource.HH_RU
        return VacancySource.URL

    @staticmethod
    def _extract_source_id(url: str) -> str:
        # hh.ru/vacancy/12345678 → "12345678"
        parts = url.rstrip("/").split("/")
        return parts[-1].split("?")[0] if parts else url
