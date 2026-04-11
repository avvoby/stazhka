import json
import logging
import random
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.events.career_week.models import CareerWeekRegistration, RoastBooking

logger = logging.getLogger(__name__)

_MAX_CODE_ATTEMPTS = 10


class CareerWeekRegistrationService:

    # ── Коды участника ────────────────────────────────────────────────────────

    async def generate_unique_code(self, session: AsyncSession) -> str:
        """Генерирует уникальный 5-значный числовой код (10000–99999)."""
        for attempt in range(_MAX_CODE_ATTEMPTS):
            code = str(random.randint(10000, 99999))
            result = await session.execute(
                text("SELECT 1 FROM career_week_registrations WHERE code = :code"),
                {"code": code},
            )
            if result.fetchone() is None:
                return code
            logger.debug("Code %s already taken, attempt %d", code, attempt + 1)
        raise RuntimeError("Не удалось сгенерировать уникальный код за 10 попыток")

    # ── Регистрация ───────────────────────────────────────────────────────────

    async def register_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        direction: str,
        program: str,
        course: str,
        skills: list[str],
    ) -> CareerWeekRegistration:
        """Регистрирует участника и возвращает объект регистрации с кодом."""
        logger.info(
            "register_user: старт — user_id=%s direction=%s program=%s course=%s",
            user_id, direction, program, course,
        )
        code = await self.generate_unique_code(session)
        reg_id = uuid4()
        now = datetime.utcnow()

        await session.execute(
            text("""
                INSERT INTO career_week_registrations
                    (id, user_id, code, direction, program, course, skills, registered_at)
                VALUES
                    (:id, :user_id, :code, :direction, :program, :course, :skills, :registered_at)
            """),
            {
                "id": reg_id,
                "user_id": user_id,
                "code": code,
                "direction": direction,
                "program": program,
                "course": course,
                "skills": json.dumps(skills, ensure_ascii=False),
                "registered_at": now,
            },
        )
        logger.info("register_user: запись в БД создана — code=%s reg_id=%s", code, reg_id)

        return CareerWeekRegistration(
            id=reg_id,
            user_id=user_id,
            code=code,
            direction=direction,
            program=program,
            course=course,
            skills=skills,
            registered_at=now,
        )

    async def get_registration(
        self, session: AsyncSession, user_id: UUID
    ) -> CareerWeekRegistration | None:
        """Возвращает регистрацию пользователя или None."""
        result = await session.execute(
            text("""
                SELECT id, user_id, code, direction, program, course, skills, registered_at
                FROM career_week_registrations
                WHERE user_id = :user_id
            """),
            {"user_id": user_id},
        )
        row = result.fetchone()
        if not row:
            return None
        return CareerWeekRegistration(
            id=row.id,
            user_id=row.user_id,
            code=row.code,
            direction=row.direction,
            program=row.program,
            course=row.course,
            skills=json.loads(row.skills) if isinstance(row.skills, str) else (row.skills or []),
            registered_at=row.registered_at,
        )

    async def is_registered(self, session: AsyncSession, user_id: UUID) -> bool:
        result = await session.execute(
            text("SELECT 1 FROM career_week_registrations WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        return result.fetchone() is not None

    # ── Прожарки ──────────────────────────────────────────────────────────────

    async def book_roast(
        self,
        session: AsyncSession,
        user_id: UUID,
        slot_id: str,
        slot_type: str,
        direction: str,
        resume_file_id: str | None,
        resume_url: str | None,
    ) -> RoastBooking:
        """
        Атомарно бронирует слот прожарки:
        - инкрементирует счётчик в career_week_slots_cache
        - создаёт запись в career_week_roast_bookings
        """
        # Инкремент счётчика (атомарно через UPDATE ... RETURNING)
        upd = await session.execute(
            text("""
                UPDATE career_week_slots_cache
                SET registrations_count = registrations_count + 1,
                    updated_at = now()
                WHERE slot_id = :slot_id
                  AND registrations_count < capacity
                RETURNING registrations_count
            """),
            {"slot_id": slot_id},
        )
        if upd.fetchone() is None:
            raise ValueError(f"Слот {slot_id} недоступен или уже заполнен")

        booking_id = uuid4()
        now = datetime.utcnow()
        await session.execute(
            text("""
                INSERT INTO career_week_roast_bookings
                    (id, user_id, slot_id, slot_type, direction,
                     resume_file_id, resume_url, booked_at)
                VALUES
                    (:id, :user_id, :slot_id, :slot_type, :direction,
                     :resume_file_id, :resume_url, :booked_at)
            """),
            {
                "id": booking_id,
                "user_id": user_id,
                "slot_id": slot_id,
                "slot_type": slot_type,
                "direction": direction,
                "resume_file_id": resume_file_id,
                "resume_url": resume_url,
                "booked_at": now,
            },
        )

        return RoastBooking(
            id=booking_id,
            user_id=user_id,
            slot_id=slot_id,
            slot_type=slot_type,
            direction=direction,
            resume_file_id=resume_file_id,
            resume_url=resume_url,
            booked_at=now,
        )

    async def cancel_booking(
        self, session: AsyncSession, booking_id: UUID, user_id: UUID
    ) -> bool:
        """
        Отменяет бронирование и уменьшает счётчик слота.
        Возвращает True если успешно.
        """
        result = await session.execute(
            text("""
                SELECT slot_id FROM career_week_roast_bookings
                WHERE id = :id AND user_id = :user_id AND cancelled_at IS NULL
            """),
            {"id": booking_id, "user_id": user_id},
        )
        row = result.fetchone()
        if not row:
            return False

        slot_id = row.slot_id
        await session.execute(
            text("""
                UPDATE career_week_roast_bookings
                SET cancelled_at = now()
                WHERE id = :id
            """),
            {"id": booking_id},
        )
        await session.execute(
            text("""
                UPDATE career_week_slots_cache
                SET registrations_count = GREATEST(registrations_count - 1, 0),
                    updated_at = now()
                WHERE slot_id = :slot_id
            """),
            {"slot_id": slot_id},
        )
        return True

    async def get_user_bookings(
        self, session: AsyncSession, user_id: UUID
    ) -> list[RoastBooking]:
        """Возвращает все активные записи пользователя."""
        result = await session.execute(
            text("""
                SELECT id, user_id, slot_id, slot_type, direction,
                       resume_file_id, resume_url, booked_at, cancelled_at
                FROM career_week_roast_bookings
                WHERE user_id = :user_id AND cancelled_at IS NULL
                ORDER BY booked_at DESC
            """),
            {"user_id": user_id},
        )
        rows = result.fetchall()
        return [
            RoastBooking(
                id=row.id,
                user_id=row.user_id,
                slot_id=row.slot_id,
                slot_type=row.slot_type,
                direction=row.direction,
                resume_file_id=row.resume_file_id,
                resume_url=row.resume_url,
                booked_at=row.booked_at,
                cancelled_at=row.cancelled_at,
            )
            for row in rows
        ]
