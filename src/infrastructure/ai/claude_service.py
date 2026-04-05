import json
import logging
import warnings
from typing import Any

import httpx

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

from src.core.config import settings
from src.domain.entities.user import UserProfile  # noqa: F401 (used in score_vacancy type hint)
from src.domain.entities.vacancy import Vacancy

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_AI_UNAVAILABLE = "AI недоступен. Попробуй позже."
_AI_UNAVAILABLE_ANALYSIS: dict[str, Any] = {
    "strengths": "",
    "improvements": "AI недоступен.",
    "ideal_answer_hint": "",
}


class ClaudeAIService:
    def __init__(self) -> None:
        api_key = settings.openrouter.api_key
        self._enabled = bool(api_key)
        self._fast_model = "anthropic/claude-haiku-3-5-20251001"
        self._quality_model = "anthropic/claude-sonnet-4-5"
        self._max_tokens = settings.openrouter.max_tokens
        self._client = httpx.AsyncClient(
            verify=False,
            timeout=30,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "stazka.app",
                "Content-Type": "application/json",
            },
        )

        if not self._enabled:
            logger.warning("OPENROUTER_API_KEY не задан — AI-функции отключены")

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def _ask(self, model: str, system: str, user: str) -> str:
        """Отправляет запрос в OpenRouter (OpenAI-совместимый формат)."""
        payload = {
            "model": model,
            "max_tokens": self._max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        logger.info("OpenRouter request: model=%s", model)
        resp = await self._client.post(_OPENROUTER_URL, json=payload)
        if not resp.is_success:
            logger.error(
                "OpenRouter error %s: %s",
                resp.status_code,
                resp.text[:500],
            )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Извлекает JSON из ответа модели, не падает при ошибке."""
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                return {}
            return json.loads(text[start:end])
        except (json.JSONDecodeError, ValueError):
            return {}

    # ── Methods ──────────────────────────────────────────────────────────────

    async def parse_user_context(self, raw_text: str) -> dict[str, Any]:
        """
        Извлекает структурированный профиль из свободного текста пользователя.
        Использует быструю модель (Haiku).
        """
        if not self._enabled:
            return {}

        system = (
            "Ты помощник, который извлекает структурированные данные из текста. "
            "Отвечай ТОЛЬКО валидным JSON без пояснений."
        )
        user = f"""Извлеки из текста данные о соискателе и верни JSON со следующими полями:
{{
  "specialization": "направление (например: backend, design, marketing)",
  "skills": ["список навыков"],
  "target_companies": ["компании или типы компаний"],
  "experience_level": "junior | middle | no_experience",
  "work_format": "office | remote | hybrid | any",
  "additional": "прочая важная информация"
}}

Если поле не удаётся определить — используй null.

Текст пользователя:
{raw_text}"""

        try:
            raw = await self._ask(self._fast_model, system, user)
            return self._parse_json(raw)
        except Exception as e:
            logger.warning("parse_user_context failed: %s", e)
            return {}

    async def generate_cover_letter(
        self, vacancy: Vacancy, profile: UserProfile | None = None
    ) -> str:
        """
        Генерирует сопроводительное письмо 150-200 слов.
        Использует быструю модель (Haiku).
        """
        if not self._enabled:
            return _AI_UNAVAILABLE

        system = (
            "Ты карьерный консультант. Пишешь сопроводительные письма "
            "на русском языке: живо, конкретно, без канцелярита. "
            "Объём — 150-200 слов."
        )
        profile_block = (profile.about if profile else "") or "Информация о профиле не указана."
        user = f"""Напиши сопроводительное письмо для отклика на стажировку.

Вакансия: {vacancy.title}
Компания: {vacancy.company}
Описание вакансии:
{vacancy.description[:1500]}

Информация о кандидате:
{profile_block}

Требования:
- Живой, не шаблонный тон
- Упомяни конкретные навыки кандидата применительно к вакансии
- Не начинай с "Уважаемые" или "Здравствуйте"
- Без подписи в конце"""

        try:
            return await self._ask(self._fast_model, system, user)
        except Exception as e:
            logger.error("generate_cover_letter failed: %s", e)
            raise

    async def generate_mock_question(
        self,
        vacancy: Vacancy,
        question_number: int,
        history: list[dict[str, str]],
    ) -> str:
        """
        Генерирует следующий вопрос mock-интервью.
        Использует качественную модель (Sonnet).
        """
        if not self._enabled:
            return _AI_UNAVAILABLE

        system = (
            f"Ты HR-менеджер из компании {vacancy.company}. "
            f"Проводишь техническое интервью на позицию «{vacancy.title}». "
            "Задавай реалистичные вопросы — поведенческие, технические, кейсовые. "
            "Учитывай предыдущие ответы кандидата. "
            "Отвечай ТОЛЬКО текстом вопроса, без пояснений."
        )

        history_block = ""
        if history:
            lines = []
            for i, turn in enumerate(history, 1):
                lines.append(f"Вопрос {i}: {turn['question']}")
                lines.append(f"Ответ {i}: {turn['answer']}")
            history_block = "\n".join(lines) + "\n\n"

        user = (
            f"Описание вакансии:\n{vacancy.description[:800]}\n\n"
            f"Требования:\n{vacancy.requirements[:500]}\n\n"
            f"{history_block}"
            f"Задай вопрос номер {question_number}."
        )

        try:
            return await self._ask(self._quality_model, system, user)
        except Exception as e:
            logger.error("generate_mock_question failed: %s", e)
            raise

    async def score_vacancy(
        self,
        vacancy: dict,
        profile: UserProfile | None = None,
    ) -> dict[str, Any]:
        """
        Оценивает соответствие вакансии профилю кандидата.
        Использует быструю модель (Haiku) для скорости в batch-режиме.
        Возвращает: {score: int 0-100, reason: str}
        """
        if not self._enabled:
            return {"score": -1, "reason": ""}

        profile_block = ""
        if profile:
            parts = []
            if profile.specialty:
                parts.append(f"Специализация: {profile.specialty}")
            if profile.skills:
                parts.append(f"Навыки: {', '.join(profile.skills)}")
            if profile.desired_position:
                parts.append(f"Желаемая должность: {profile.desired_position}")
            if profile.desired_city:
                parts.append(f"Желаемый город: {profile.desired_city}")
            profile_block = "\n".join(parts)

        system = (
            "Ты рекрутер, оцениваешь соответствие вакансии профилю кандидата. "
            "Отвечай ТОЛЬКО валидным JSON без пояснений."
        )
        user = f"""Оцени соответствие вакансии профилю кандидата по шкале 0-100.

Вакансия: {vacancy.get('title', '')} — {vacancy.get('company', '')}
Описание: {(vacancy.get('description') or '')[:500]}
Требования: {(vacancy.get('requirements') or '')[:300]}

Профиль кандидата:
{profile_block or 'Не указан'}

Верни JSON:
{{
  "score": 85,
  "reason": "Краткое объяснение 1-2 предложения"
}}"""

        try:
            raw = await self._ask(self._fast_model, system, user)
            parsed = self._parse_json(raw)
            if not parsed or "score" not in parsed:
                return {"score": -1, "reason": ""}
            return {"score": int(parsed["score"]), "reason": str(parsed.get("reason", ""))}
        except Exception as e:
            logger.debug("score_vacancy failed: %s", e)
            return {"score": -1, "reason": ""}

    async def analyze_mock_answer(
        self,
        question: str,
        answer: str,
        vacancy: Vacancy,
    ) -> dict[str, Any]:
        """
        Анализирует ответ кандидата на mock-интервью.
        Использует качественную модель (Sonnet).
        Возвращает: {strengths, improvements, ideal_answer_hint}
        """
        if not self._enabled:
            return _AI_UNAVAILABLE_ANALYSIS

        system = (
            f"Ты опытный HR из компании {vacancy.company}. "
            "Оцениваешь ответы кандидата на интервью. "
            "Отвечай ТОЛЬКО валидным JSON без пояснений."
        )
        user = f"""Оцени ответ кандидата на вопрос интервью.

Позиция: {vacancy.title}
Вопрос: {question}
Ответ кандидата: {answer}

Верни JSON:
{{
  "strengths": "что кандидат сделал хорошо",
  "improvements": "что стоит улучшить или добавить",
  "ideal_answer_hint": "подсказка — как выглядел бы сильный ответ"
}}"""

        try:
            raw = await self._ask(self._quality_model, system, user)
            parsed = self._parse_json(raw)
            if not parsed:
                return {"strengths": "", "improvements": raw, "ideal_answer_hint": ""}
            return parsed
        except Exception as e:
            logger.error("analyze_mock_answer failed: %s", e)
            return {
                "strengths": "",
                "improvements": f"Не удалось получить анализ: {e}",
                "ideal_answer_hint": "",
            }

    async def generate_mock_report(
        self,
        history: list[dict[str, str]],
        vacancy_title: str,
        company: str,
    ) -> str:
        """
        Генерирует итоговый отчёт по всему mock-интервью.
        Использует качественную модель (Sonnet).
        Возвращает текстовый отчёт: оценка A/B/C + рекомендации.
        """
        if not self._enabled:
            return _AI_UNAVAILABLE

        history_block = ""
        for i, turn in enumerate(history, 1):
            history_block += f"Вопрос {i}: {turn['question']}\nОтвет {i}: {turn['answer']}\n\n"

        system = (
            f"Ты опытный HR-консультант. Оцениваешь итоги mock-интервью кандидата "
            f"на позицию «{vacancy_title}» в компании {company}. "
            "Пиши на русском. Будь конкретен, честен, но конструктивен."
        )
        user = f"""Оцени всё интервью целиком и напиши итоговый отчёт.

История интервью:
{history_block}

Структура отчёта:
Общая оценка: [A / B+ / B / C+  / C — выбери одну] — одна фраза-объяснение

💪 Сильные стороны (топ-3):
— ...

🎯 Зоны роста (топ-3):
— ...

📝 Рекомендации перед реальным интервью (3 конкретных совета):
1. ...
2. ...
3. ...

Пиши лаконично, без воды. Максимум 250 слов."""

        try:
            return await self._ask(self._quality_model, system, user)
        except Exception as e:
            logger.error("generate_mock_report failed: %s", e)
            return "Не удалось сгенерировать отчёт. Попробуй позже."
