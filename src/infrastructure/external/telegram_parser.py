"""
Парсер вакансий из Telegram-каналов через Telethon (MTProto).

Требует TELEGRAM_API_ID и TELEGRAM_API_HASH — не бот-токен!
Сессия сохраняется в файл stazka_parser.session рядом с точкой запуска.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from src.core.config import settings

logger = logging.getLogger(__name__)

# Ключевые слова для фильтрации сообщений о вакансиях
_VACANCY_KEYWORDS = [
    "стажировк", "стажёр", "стажер", "intern", "internship",
    "junior", "джуниор", "вакансия", "вакансии", "набор",
    "ищем", "открыта позиция", "открытая позиция",
]

# Паттерны для извлечения ссылок на вакансии
_URL_PATTERN = re.compile(r"https?://\S+")


class TelegramChannelParser:
    """
    Читает последние сообщения из Telegram-каналов и извлекает объявления
    о вакансиях/стажировках.

    Использует Telethon (MTProto), не бот-токен.
    При отсутствии API-ключей возвращает пустой список без ошибки.
    """

    def __init__(self) -> None:
        self._api_id = settings.telegram.api_id
        self._api_hash = settings.telegram.api_hash
        self._channels = settings.telegram.channels_list
        self._enabled = bool(self._api_id and self._api_hash and self._channels)

        if not self._enabled:
            logger.info(
                "Telegram parser отключён: "
                "TELEGRAM_API_ID / TELEGRAM_API_HASH / TELEGRAM_CHANNELS не заданы"
            )

    async def fetch_vacancies(
        self,
        days: int = 7,
        limit_per_channel: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Парсит каналы и возвращает список унифицированных dict вакансий.
        Если Telethon не установлен или ключи не заданы — возвращает [].
        """
        if not self._enabled:
            return []

        try:
            from telethon import TelegramClient  # type: ignore[import]
            from telethon.tl.types import Message  # type: ignore[import]
        except ImportError:
            logger.warning("Telethon не установлен — пропускаем парсинг каналов")
            return []

        since = datetime.now(tz=timezone.utc) - timedelta(days=days)
        results: list[dict[str, Any]] = []

        client = TelegramClient(
            "stazka_parser",
            self._api_id,
            self._api_hash,
        )

        try:
            await client.start()  # type: ignore[call-arg]
            for channel in self._channels:
                try:
                    channel_results = await self._parse_channel(
                        client, channel, since, limit_per_channel
                    )
                    results.extend(channel_results)
                    logger.info(
                        "Канал @%s: найдено %d вакансий",
                        channel,
                        len(channel_results),
                    )
                except Exception as e:
                    logger.warning("Ошибка парсинга канала @%s: %s", channel, e)
        finally:
            await client.disconnect()  # type: ignore[call-arg]

        logger.info("Telegram parser итого: %d вакансий из %d каналов", len(results), len(self._channels))
        return results

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    async def _parse_channel(
        client: Any,
        channel: str,
        since: datetime,
        limit: int,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        async for message in client.iter_messages(channel, limit=limit):
            if not message.text:
                continue
            if message.date.replace(tzinfo=timezone.utc) < since:
                break
            if not TelegramChannelParser._is_vacancy(message.text):
                continue
            results.append(TelegramChannelParser._normalize(message, channel))
        return results

    @staticmethod
    def _is_vacancy(text: str) -> bool:
        """Проверяет, содержит ли текст ключевые слова вакансии."""
        lower = text.lower()
        return any(kw in lower for kw in _VACANCY_KEYWORDS)

    @staticmethod
    def _normalize(message: Any, channel: str) -> dict[str, Any]:
        """Приводит Telegram-сообщение к унифицированному dict агрегатора."""
        text: str = message.text or ""
        urls = _URL_PATTERN.findall(text)
        url = urls[0] if urls else f"https://t.me/{channel}/{message.id}"

        # Первая строка обычно — название вакансии
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        title = lines[0][:120] if lines else "Вакансия из Telegram"

        return {
            "source": "telegram",
            "source_id": f"tg_{channel}_{message.id}",
            "title": title,
            "company": f"@{channel}",
            "city": "",
            "description": text[:3000],
            "requirements": "",
            "url": url,
            "salary_from": None,
            "salary_to": None,
            "currency": "RUB",
            "published_at": message.date,
        }
