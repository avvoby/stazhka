"""POST /api/chat — endpoint AI-наставника для Telegram Mini App.

Принимает историю сообщений + профиль студента, возвращает ответ Claude
через OpenRouter. Простой in-memory rate-limit 5 запросов/день/Telegram-юзер
(сбрасывается при рестарте api-контейнера; для прода переехать на Redis).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.infrastructure.ai.claude_service import ClaudeAIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Singleton — переиспользуем httpx.AsyncClient между запросами
_claude = ClaudeAIService()

# In-memory лимит: (tg_user_id, date_iso) → count
_DAILY_LIMIT = 5
_counter: dict[tuple[int, str], int] = defaultdict(int)


def _check_limit(tg_user_id: int) -> tuple[bool, int]:
    """Возвращает (ok, remaining_after_this). ok=False если лимит исчерпан."""
    today = date.today().isoformat()
    key = (tg_user_id, today)
    used = _counter[key]
    if used >= _DAILY_LIMIT:
        return False, 0
    _counter[key] = used + 1
    return True, _DAILY_LIMIT - (used + 1)


# ── Schemas ──────────────────────────────────────────────────────────────


class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatProfile(BaseModel):
    fio: str = ""
    course: str | None = None
    program: str | None = None
    direction: str | None = None
    companies: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    tg_user_id: int = Field(..., description="Telegram user.id")
    messages: list[Message] = Field(..., min_length=1, max_length=20)
    profile: ChatProfile | None = None


class ChatResponse(BaseModel):
    text: str
    remaining: int


# ── System prompt ────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """\
Ты — карьерный наставник продукта «Стажка» для студентов ВШБ НИУ ВШЭ.
Помогаешь искать стажировку, готовиться к отбору, дорабатывать резюме и cover letter,
разбирать кейс-интервью.

Тон: спокойный, уверенный, лаконичный. Без эмоджи. Без слов «ура», «вау», «супер».
Без шапки и подписи — только сам ответ. Не льсти.

Форматирование: короткие абзацы. Markdown для жирного и списков. Если уместно —
конкретные примеры компаний, сроков (опираясь на 2026 год).

Если в профиле студента не хватает данных для точного ответа — задай ОДИН уточняющий
вопрос, не списком.

Профиль студента:
{profile}
"""


def _format_profile(profile: ChatProfile | None) -> str:
    if not profile:
        return "(пусто)"
    parts: list[str] = []
    if profile.fio:
        parts.append(f"имя: {profile.fio}")
    if profile.course:
        parts.append(f"курс: {profile.course}")
    if profile.program:
        parts.append(f"программа: {profile.program}")
    if profile.direction:
        parts.append(f"направление: {profile.direction}")
    if profile.companies:
        parts.append(f"компании мечты: {', '.join(profile.companies)}")
    return " · ".join(parts) if parts else "(пусто)"


# ── Endpoint ─────────────────────────────────────────────────────────────


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    if not _claude.is_enabled:
        raise HTTPException(status_code=503, detail="AI temporarily unavailable")

    ok, remaining = _check_limit(req.tg_user_id)
    if not ok:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit ({_DAILY_LIMIT}) reached. Try tomorrow.",
        )

    system = SYSTEM_PROMPT_TEMPLATE.format(profile=_format_profile(req.profile))

    try:
        text = await _claude.chat_completion(
            system=system,
            messages=[m.model_dump() for m in req.messages],
        )
    except Exception as e:
        logger.exception("Claude call failed")
        raise HTTPException(status_code=502, detail="AI provider error") from e

    return ChatResponse(text=text, remaining=remaining)
