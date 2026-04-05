import logging
from datetime import datetime
from typing import Any

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)

_SJ_API_BASE = "https://api.superjob.ru/2.0"

# Маппинг специализации → SuperJob keyword
SPEC_TO_QUERY_SJ: dict[str, str] = {
    "Финансы":     "финансовый аналитик стажёр",
    "Консалтинг":  "консультант стажёр",
    "Маркетинг":   "маркетолог стажёр",
    "HR":          "HR стажёр",
    "Операции":    "операционный менеджер стажёр",
    "IT":          "программист стажёр",
}


class SuperJobClient:
    def __init__(self) -> None:
        api_key = settings.superjob.api_key
        self._enabled = bool(api_key)
        self._client = httpx.AsyncClient(
            base_url=_SJ_API_BASE,
            headers={
                "X-Api-App-Id": api_key,
                "Accept": "application/json",
            },
            timeout=10.0,
        )
        if not self._enabled:
            logger.info("SUPERJOB_API_KEY не задан — SuperJob отключён")

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "SuperJobClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def search_vacancies(
        self, query: str, count: int = 50
    ) -> list[dict[str, Any]]:
        """
        Ищет вакансии на SuperJob.
        Возвращает список сырых dict в унифицированном формате агрегатора.
        """
        if not self._enabled:
            return []

        params: dict[str, Any] = {
            "keyword": query,
            "no_agreement": 1,   # только с указанной зарплатой (или стажировки)
            "count": count,
            "town": 4,           # Москва
        }

        try:
            resp = await self._client.get("/vacancies/", params=params)
            resp.raise_for_status()
            data = resp.json()
            items: list[dict[str, Any]] = data.get("objects", [])
            return [self._normalize(item) for item in items]
        except httpx.TimeoutException:
            logger.warning("SuperJob search timeout for query=%r", query)
            return []
        except httpx.HTTPStatusError as e:
            logger.warning("SuperJob search HTTP error: %s", e)
            return []
        except Exception as e:
            logger.error("SuperJob search unexpected error: %s", e)
            return []

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
        """Приводит SuperJob vacancy к унифицированному dict агрегатора."""
        salary_from: int | None = raw.get("payment_from") or None
        salary_to: int | None = raw.get("payment_to") or None
        currency: str = raw.get("currency", "rub").upper()

        date_published = raw.get("date_published")
        published_at: datetime | None = None
        if date_published:
            try:
                published_at = datetime.fromtimestamp(date_published)
            except (OSError, ValueError, OverflowError):
                pass

        return {
            "source": "superjob",
            "source_id": str(raw.get("id", "")),
            "title": raw.get("profession", ""),
            "company": (raw.get("firm_name") or ""),
            "city": (raw.get("town") or {}).get("title", ""),
            "description": raw.get("vacancyRichText") or raw.get("candidat", ""),
            "requirements": raw.get("candidat", ""),
            "url": raw.get("link", ""),
            "salary_from": salary_from,
            "salary_to": salary_to,
            "currency": currency,
            "published_at": published_at,
        }
