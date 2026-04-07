"""
Redis-кэш для данных Весенней недели карьеры.
sync_from_sheets() читает всё из Google Sheets и кладёт в Redis.
"""
import json
import logging

from redis.asyncio import Redis
from sqlalchemy import text

from src.events.career_week.config import career_week_settings
from src.events.career_week.models import RoastSlot
from src.events.career_week.services.sheets import GoogleSheetsService
from src.infrastructure.database.connection import AsyncSessionFactory

logger = logging.getLogger(__name__)

_TTL = 86400  # 24 часа
_PREFIX = "cw:"


class CareerWeekCacheService:

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    # ── Синхронизация ─────────────────────────────────────────────────────────

    async def sync_from_sheets(self, sheets: GoogleSheetsService) -> dict:
        """
        Читает все данные из Google Sheets, сохраняет в Redis,
        инициализирует/обновляет capacity слотов в БД.
        Возвращает статистику {"partners": N, ...}.
        """
        partners = await sheets.get_partners()
        schedule = await sheets.get_schedule()
        roast_slots = await sheets.get_roast_slots()
        programs = await sheets.get_programs()
        admins = await sheets.get_admins()
        skills = await sheets.get_skills()

        await self._redis.setex(_PREFIX + "partners", _TTL, json.dumps(partners, ensure_ascii=False))
        await self._redis.setex(_PREFIX + "schedule", _TTL, json.dumps(schedule, ensure_ascii=False))
        await self._redis.setex(_PREFIX + "roast_slots", _TTL, json.dumps(roast_slots, ensure_ascii=False))
        await self._redis.setex(_PREFIX + "programs", _TTL, json.dumps(programs, ensure_ascii=False))
        await self._redis.setex(_PREFIX + "admins", _TTL, json.dumps(admins, ensure_ascii=False))
        await self._redis.setex(_PREFIX + "skills", _TTL, json.dumps(skills, ensure_ascii=False))

        # Инициализируем/обновляем слоты в БД
        if roast_slots:
            async with AsyncSessionFactory() as session:
                for slot in roast_slots:
                    slot_id = str(slot.get("id", ""))
                    capacity = int(slot.get("capacity", 0))
                    if not slot_id:
                        continue
                    await session.execute(
                        text("""
                            INSERT INTO career_week_slots_cache
                                (slot_id, capacity, registrations_count, updated_at)
                            VALUES
                                (:slot_id, :capacity, 0, now())
                            ON CONFLICT (slot_id) DO UPDATE
                                SET capacity = excluded.capacity,
                                    updated_at = now()
                        """),
                        {"slot_id": slot_id, "capacity": capacity},
                    )
                await session.commit()

        stats = {
            "partners": len(partners),
            "schedule": len(schedule),
            "roast_slots": len(roast_slots),
            "programs": len(programs),
            "skills": len(skills),
        }
        logger.info("CareerWeek кэш синхронизирован: %s", stats)
        return stats

    # ── Геттеры ───────────────────────────────────────────────────────────────

    async def get_partners(self) -> list[dict]:
        raw = await self._redis.get(_PREFIX + "partners")
        if not raw:
            return []
        return json.loads(raw)  # type: ignore[no-any-return]

    async def get_schedule(self) -> list[dict]:
        raw = await self._redis.get(_PREFIX + "schedule")
        if not raw:
            return []
        return json.loads(raw)  # type: ignore[no-any-return]

    async def get_roast_slots(self) -> list[RoastSlot]:
        raw = await self._redis.get(_PREFIX + "roast_slots")
        if not raw:
            return []
        slots_data: list[dict] = json.loads(raw)

        # Читаем счётчики из БД одним запросом
        slot_ids = [str(s.get("id", "")) for s in slots_data if s.get("id")]
        counts: dict[str, int] = {}
        if slot_ids:
            async with AsyncSessionFactory() as session:
                result = await session.execute(
                    text("""
                        SELECT slot_id, registrations_count
                        FROM career_week_slots_cache
                        WHERE slot_id = ANY(:ids)
                    """),
                    {"ids": slot_ids},
                )
                for row in result.fetchall():
                    counts[row.slot_id] = row.registrations_count

        return [
            RoastSlot(
                id=str(s.get("id", "")),
                type=str(s.get("type", "")),
                date=str(s.get("date", "")),
                time=str(s.get("time", "")),
                direction=str(s.get("direction", "")),
                capacity=int(s.get("capacity", 0)),
                registrations_count=counts.get(str(s.get("id", "")), 0),
            )
            for s in slots_data
            if s.get("id")
        ]

    async def get_programs(self) -> list[dict]:
        """Возвращает все программы как list[dict] с ключами name, level."""
        raw = await self._redis.get(_PREFIX + "programs")
        if not raw:
            return []
        return json.loads(raw)  # type: ignore[no-any-return]

    async def get_programs_by_level(self, level: str) -> list[str]:
        """Возвращает названия программ для указанного уровня образования."""
        programs = await self.get_programs()
        level_lower = level.strip().lower()
        return [p["name"] for p in programs if p.get("level", "") == level_lower]

    _DEFAULT_SKILLS: list[str] = [
        "Excel", "Python", "SQL", "PowerPoint", "Финмодели",
        "Figma", "VBA", "R", "Tableau", "Power BI", "Bloomberg", "1С",
        "Английский B2+", "Английский C1+", "Немецкий",
        "Французский", "Китайский", "Испанский",
        "Управление проектами", "Публичные выступления", "Аналитическое мышление",
    ]

    async def get_skills(self) -> list[str]:
        raw = await self._redis.get(_PREFIX + "skills")
        if not raw:
            return self._DEFAULT_SKILLS
        data: list[str] = json.loads(raw)
        return data if data else self._DEFAULT_SKILLS

    async def get_admins(self) -> list[int]:
        raw = await self._redis.get(_PREFIX + "admins")
        if not raw:
            return []
        return json.loads(raw)  # type: ignore[no-any-return]

    async def is_admin(self, telegram_id: int) -> bool:
        if telegram_id in career_week_settings.career_week_admin_ids:
            return True
        admins = await self.get_admins()
        return telegram_id in admins
