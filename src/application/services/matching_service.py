"""
3-уровневый матчинг вакансий:

  Уровень 1 — Жёсткий фильтр по специализации (ключевые слова)
  Уровень 2 — Keyword scoring (навыки, должность, город) — быстро, без AI
  Уровень 3 — Claude scoring — только top-20 по keyword_score → финальный top-5
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from src.domain.entities.user import UserProfile

logger = logging.getLogger(__name__)

# ── Ключевые слова по специализациям ─────────────────────────────────────────

SPEC_KEYWORDS: dict[str, list[str]] = {
    # Русские ключи (из онбординга)
    "Финансы":    ["финанс", "бухгалтер", "казначей", "инвестиц", "банк", "аудит"],
    "Консалтинг": ["консульт", "аналитик", "стратег", "советник", "mckinsey", "bcg"],
    "Маркетинг":  ["маркетинг", "smm", "pr", "реклам", "бренд", "продвижени"],
    "HR":         ["hr", "кадр", "персонал", "рекрутинг", "подбор"],
    "Операции":   ["операци", "логистик", "supply", "процесс", "проект"],
    "IT":         ["разработ", "программ", "frontend", "backend", "data", "python", "java"],
    # Английские ключи (на случай если хранится по-английски)
    "finance":    ["финанс", "бухгалтер", "казначей", "инвестиц", "банк", "аудит"],
    "consulting": ["консульт", "аналитик", "стратег", "советник"],
    "marketing":  ["маркетинг", "smm", "pr", "реклам", "бренд"],
    "hr":         ["hr", "кадр", "персонал", "рекрутинг"],
    "operations": ["операци", "логистик", "supply", "процесс"],
    "it":         ["разработ", "программ", "frontend", "backend", "data"],
}

_GENERIC_KEYWORDS = ["стажировк", "intern", "junior", "практик", "student", "студент"]


@dataclass
class ScoredVacancy:
    vacancy: dict[str, Any]
    keyword_score: int = 0       # 0–100
    claude_score: int = -1       # 0–100, -1 если не оценивался
    reason: str = ""             # объяснение Claude
    source: str = ""             # "hh" | "superjob" | "telegram"

    @property
    def final_score(self) -> int:
        return self.claude_score if self.claude_score >= 0 else self.keyword_score


class MatchingService:
    """
    Принимает список унифицированных dict вакансий и UserProfile,
    возвращает топ-N ScoredVacancy.
    """

    def __init__(self, ai_service: object) -> None:
        self._ai = ai_service

    async def match(
        self,
        vacancies: list[dict[str, Any]],
        profile: UserProfile | None,
    ) -> list[ScoredVacancy]:
        if not vacancies:
            return []

        # Уровень 1 — жёсткий фильтр
        filtered = self._hard_filter(vacancies, profile)
        logger.info("Matching L1 (hard filter): %d → %d", len(vacancies), len(filtered))

        # Уровень 2 — keyword scoring
        scored = [self._keyword_score(v, profile) for v in filtered]
        scored.sort(key=lambda x: x.keyword_score, reverse=True)
        logger.info("Matching L2 (keyword): top score = %d", scored[0].keyword_score if scored else 0)

        # Уровень 3 — Claude scoring (только top-40)
        top40 = scored[:40]
        await self._claude_score_batch(top40, profile)

        # Финальная сортировка — возвращаем ВСЕ, обрезка в handler
        top40.sort(key=lambda x: x.final_score, reverse=True)
        return top40

    # ── Уровень 1: Жёсткий фильтр ────────────────────────────────────────────

    def _hard_filter(
        self,
        vacancies: list[dict[str, Any]],
        profile: UserProfile | None,
    ) -> list[dict[str, Any]]:
        specialty = (profile.specialty if profile else "") or ""

        # Ищем регистронезависимо: сначала как есть, потом lower
        keywords = (
            SPEC_KEYWORDS.get(specialty)
            or SPEC_KEYWORDS.get(specialty.lower())
        )
        if not keywords:
            logger.warning("Unknown specialty: %r, skipping hard filter", specialty)
            return vacancies

        result = []
        for v in vacancies:
            text = self._vacancy_text(v)
            if any(kw in text for kw in keywords):
                result.append(v)
        return result

    # ── Уровень 2: Keyword scoring ────────────────────────────────────────────

    def _keyword_score(
        self,
        vacancy: dict[str, Any],
        profile: UserProfile | None,
    ) -> ScoredVacancy:
        text = self._vacancy_text(vacancy)

        # Базовый score для всех вакансий — гарантирует показ даже при пустом профиле
        score = 30

        if profile:
            # +10 за каждый навык из профиля, найденный в тексте вакансии
            for skill in (profile.skills or []):
                if skill.lower() in text:
                    score += 10

            # +15 за желаемую должность
            if profile.desired_position and profile.desired_position.lower() in text:
                score += 15

            # +10 за совпадение города
            if profile.desired_city and profile.desired_city.lower() in (vacancy.get("city") or "").lower():
                score += 10

            # +5 за специализацию
            specialty = profile.specialty or ""
            keywords = (
                SPEC_KEYWORDS.get(specialty)
                or SPEC_KEYWORDS.get(specialty.lower())
                or []
            )
            if any(kw in text for kw in keywords):
                score += 5

        score = min(score, 100)
        return ScoredVacancy(
            vacancy=vacancy,
            keyword_score=score,
            source=vacancy.get("source", ""),
        )

    # ── Уровень 3: Claude scoring ─────────────────────────────────────────────

    async def _claude_score_batch(
        self,
        items: list[ScoredVacancy],
        profile: UserProfile | None,
    ) -> None:
        """Параллельно оценивает вакансии через Claude. Ошибки не критичны."""
        tasks = [
            asyncio.create_task(self._claude_score_one(item, profile))
            for item in items
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _claude_score_one(
        self,
        item: ScoredVacancy,
        profile: UserProfile | None,
    ) -> None:
        try:
            result: dict[str, Any] = await self._ai.score_vacancy(  # type: ignore[attr-defined]
                vacancy=item.vacancy,
                profile=profile,
            )
            item.claude_score = int(result.get("score", -1))
            item.reason = result.get("reason", "")
        except Exception as e:
            logger.debug("Claude scoring failed for vacancy %s: %s", item.vacancy.get("source_id"), e)
            # Оставляем claude_score = -1, используется keyword_score

    # ── Utils ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _vacancy_text(vacancy: dict[str, Any]) -> str:
        return " ".join([
            (vacancy.get("title") or ""),
            (vacancy.get("description") or ""),
            (vacancy.get("requirements") or ""),
        ]).lower()
