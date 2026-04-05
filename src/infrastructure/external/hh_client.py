import logging
import re
from typing import Any

import httpx

from src.domain.entities.vacancy import Vacancy
from src.domain.value_objects.vacancy_source import VacancySource
from src.domain.value_objects.work_format import WorkFormat

logger = logging.getLogger(__name__)

HH_API_BASE = "https://api.hh.ru"

# Маппинг специализации профиля → поисковый запрос на hh.ru
SPEC_TO_QUERY: dict[str, str] = {
    "Финансы":     "финансовый аналитик",
    "Консалтинг":  "консультант аналитик",
    "Маркетинг":   "маркетолог",
    "HR":          "HR менеджер",
    "Операции":    "операционный менеджер",
    "IT":          "разработчик программист",
}

# Навыки, которые имеет смысл добавлять в поисковый запрос
TECH_SKILLS_FOR_QUERY: set[str] = {"Excel", "Python", "SQL", "Figma", "PowerPoint"}

HH_SCHEDULE_TO_WORK_FORMAT: dict[str, WorkFormat] = {
    "remote": WorkFormat.REMOTE,
    "fullDay": WorkFormat.OFFICE,
    "shift": WorkFormat.OFFICE,
    "flexible": WorkFormat.HYBRID,
    "flyInFlyOut": WorkFormat.OFFICE,
}


class HHClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=HH_API_BASE,
            headers={
                "User-Agent": "stazka/1.0 (telegram bot)",
                "Accept": "application/json",
            },
            timeout=10.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "HHClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    # ── Public methods ────────────────────────────────────────────────────────

    async def search_vacancies(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Ищет вакансии на hh.ru — две страницы параллельно (до 100 результатов).
        filters опциональны: experience, area, salary, schedule.
        """
        import asyncio as _asyncio

        base_params: dict[str, Any] = {
            "text": query,
            "area": 1,
            "per_page": 50,
            "search_field": "name",
            "only_with_vacancies": "true",
        }
        if filters:
            base_params.update(filters)

        async def _fetch_page(page: int) -> list[dict[str, Any]]:
            params = {**base_params, "page": page}
            try:
                response = await self._client.get("/vacancies", params=params)
                response.raise_for_status()
                return response.json().get("items", [])
            except httpx.TimeoutException:
                logger.warning("hh.ru search timeout query=%r page=%d", query, page)
                return []
            except httpx.HTTPStatusError as e:
                logger.warning("hh.ru search HTTP error page=%d: %s", page, e)
                return []
            except Exception as e:
                logger.error("hh.ru search unexpected error page=%d: %s", page, e)
                return []

        page0, page1 = await _asyncio.gather(_fetch_page(0), _fetch_page(1))
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for item in page0 + page1:
            vid = str(item.get("id", ""))
            if vid and vid not in seen:
                seen.add(vid)
                result.append(item)
        return result

    async def search_vacancies_broad(self, query: str) -> list[dict[str, Any]]:
        """Поиск без фильтра experience — для расширенного поиска."""
        return await self.search_vacancies(query, filters={"area": 1})

    async def get_vacancy(self, vacancy_id: str) -> dict[str, Any] | None:
        """
        Возвращает полные данные вакансии или None при 404.
        """
        try:
            response = await self._client.get(f"/vacancies/{vacancy_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.warning("hh.ru get_vacancy timeout for id=%r", vacancy_id)
            return None
        except httpx.HTTPStatusError as e:
            logger.warning("hh.ru get_vacancy HTTP error: %s", e)
            return None
        except Exception as e:
            logger.error("hh.ru get_vacancy unexpected error: %s", e)
            return None

    async def fetch_vacancy_by_url(self, url: str) -> Vacancy | None:
        """
        Парсит вакансию по URL hh.ru и возвращает domain Vacancy.
        Возвращает None если URL не распознан или запрос упал.
        """
        vacancy_id = self.parse_hh_url(url)
        if not vacancy_id:
            return None
        raw = await self.get_vacancy(vacancy_id)
        if not raw:
            return None
        return self.vacancy_to_domain(raw)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def parse_hh_url(url: str) -> str | None:
        """
        Извлекает vacancy_id из URL вида:
          https://hh.ru/vacancy/123456
          https://spb.hh.ru/vacancy/123456?query=...
          https://headhunter.ru/vacancy/123456
        Возвращает "123456" или None.
        """
        pattern = r"(?:hh\.ru|headhunter\.ru)/vacancy/(\d+)"
        match = re.search(pattern, url)
        return match.group(1) if match else None

    @staticmethod
    def vacancy_to_domain(raw: dict[str, Any]) -> Vacancy:
        """Маппит сырой ответ hh.ru API в domain-сущность Vacancy."""
        salary_from: int | None = None
        salary_to: int | None = None
        salary_currency = "RUB"

        if raw.get("salary"):
            salary = raw["salary"]
            salary_from = salary.get("from")
            salary_to = salary.get("to")
            salary_currency = salary.get("currency", "RUB")

        schedule_id: str = (raw.get("schedule") or {}).get("id", "")
        work_format = HH_SCHEDULE_TO_WORK_FORMAT.get(schedule_id, WorkFormat.UNSPECIFIED)

        # description приходит в HTML — берём как есть, очистим на уровне UI
        description: str = raw.get("description", "")
        requirements: str = ""
        snippet = raw.get("snippet") or {}
        if snippet.get("requirement"):
            requirements = snippet["requirement"]

        employer: dict[str, Any] = raw.get("employer") or {}
        area: dict[str, Any] = raw.get("area") or {}

        return Vacancy(
            title=raw.get("name", ""),
            company=employer.get("name", ""),
            description=description,
            requirements=requirements,
            city=area.get("name", ""),
            work_format=work_format,
            salary_from=salary_from,
            salary_to=salary_to,
            salary_currency=salary_currency,
            source=VacancySource.HH_RU,
            source_url=raw.get("alternate_url", ""),
            source_id=str(raw.get("id", "")),
        )
