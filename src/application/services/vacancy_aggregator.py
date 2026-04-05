"""
Параллельный сбор вакансий из всех доступных источников:
  - hh.ru (всегда)
  - SuperJob (если SUPERJOB_API_KEY задан)
  - Telegram-каналы (если TELEGRAM_API_ID / API_HASH / CHANNELS заданы)

Возвращает список унифицированных dict с полем `source`.
"""
import asyncio
import logging
from typing import Any

from src.domain.entities.user import UserProfile
from src.infrastructure.external.hh_client import HHClient, SPEC_TO_QUERY, TECH_SKILLS_FOR_QUERY
from src.infrastructure.external.superjob_client import SuperJobClient, SPEC_TO_QUERY_SJ
from src.infrastructure.external.telegram_parser import TelegramChannelParser

logger = logging.getLogger(__name__)


def _build_hh_query(profile: UserProfile | None) -> str:
    specialty = profile.specialty if profile else ""
    base = SPEC_TO_QUERY.get(specialty, specialty or "стажировка")
    if profile and profile.skills:
        tech = [s for s in profile.skills if s in TECH_SKILLS_FOR_QUERY]
        if tech:
            base += " " + " ".join(tech[:2])
    return base


def _build_sj_query(profile: UserProfile | None) -> str:
    specialty = profile.specialty if profile else ""
    return SPEC_TO_QUERY_SJ.get(specialty, specialty or "стажировка")


def _normalize_hh(raw: dict[str, Any]) -> dict[str, Any]:
    """Приводит сырой ответ hh.ru к унифицированному dict агрегатора."""
    employer = raw.get("employer") or {}
    area = raw.get("area") or {}
    salary = raw.get("salary") or {}
    snippet = raw.get("snippet") or {}

    return {
        "source": "hh",
        "source_id": str(raw.get("id", "")),
        "title": raw.get("name", ""),
        "company": employer.get("name", ""),
        "city": area.get("name", ""),
        "description": (snippet.get("responsibility") or ""),
        "requirements": (snippet.get("requirement") or ""),
        "url": raw.get("alternate_url", ""),
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "currency": salary.get("currency", "RUB"),
        "published_at": raw.get("published_at"),
    }


class VacancyAggregator:
    """
    Параллельно собирает вакансии из hh.ru, SuperJob и Telegram-каналов.
    Каждый источник работает независимо — ошибка одного не ломает остальные.
    """

    def __init__(
        self,
        hh_client: HHClient,
        superjob_client: SuperJobClient,
        telegram_parser: TelegramChannelParser,
    ) -> None:
        self._hh = hh_client
        self._sj = superjob_client
        self._tg = telegram_parser

    async def fetch_all(
        self,
        profile: UserProfile | None,
        hh_filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Параллельно собирает вакансии из всех источников.
        Возвращает объединённый список унифицированных dict.
        """
        hh_query = _build_hh_query(profile)
        sj_query = _build_sj_query(profile)

        hh_task = asyncio.create_task(
            self._fetch_hh(hh_query, hh_filters or {"experience": "noExperience", "per_page": 20, "area": 1})
        )
        sj_task = asyncio.create_task(self._fetch_sj(sj_query))
        tg_task = asyncio.create_task(self._fetch_tg())

        hh_results, sj_results, tg_results = await asyncio.gather(
            hh_task, sj_task, tg_task, return_exceptions=False
        )

        all_vacancies: list[dict[str, Any]] = []
        all_vacancies.extend(hh_results)   # type: ignore[arg-type]
        all_vacancies.extend(sj_results)   # type: ignore[arg-type]
        all_vacancies.extend(tg_results)   # type: ignore[arg-type]

        logger.info(
            "Aggregator: hh=%d, superjob=%d, telegram=%d, total=%d",
            len(hh_results),   # type: ignore[arg-type]
            len(sj_results),   # type: ignore[arg-type]
            len(tg_results),   # type: ignore[arg-type]
            len(all_vacancies),
        )
        return all_vacancies

    async def _fetch_hh(self, query: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            raw_list = await self._hh.search_vacancies(query, filters)
            if len(raw_list) < 5:
                logger.info("hh.ru: мало результатов (%d), расширяем поиск без фильтра experience", len(raw_list))
                broad = await self._hh.search_vacancies_broad(query)
                # Добавляем только новые
                seen = {str(r.get("id")) for r in raw_list}
                for r in broad:
                    if str(r.get("id")) not in seen:
                        raw_list.append(r)
                        seen.add(str(r.get("id")))
            return [_normalize_hh(r) for r in raw_list]
        except Exception as e:
            logger.error("hh.ru aggregation failed: %s", e)
            return []

    async def _fetch_sj(self, query: str) -> list[dict[str, Any]]:
        try:
            return await self._sj.search_vacancies(query)
        except Exception as e:
            logger.error("SuperJob aggregation failed: %s", e)
            return []

    async def _fetch_tg(self) -> list[dict[str, Any]]:
        try:
            return await self._tg.fetch_vacancies()
        except Exception as e:
            logger.error("Telegram aggregation failed: %s", e)
            return []
