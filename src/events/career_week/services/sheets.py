"""
Google Sheets интеграция для модуля Весенней недели карьеры.
Все методы async — IO делегируется в asyncio.to_thread().
"""
import asyncio
import json
import logging
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from src.events.career_week.config import career_week_settings
from src.events.career_week.models import CareerWeekRegistration, RoastBooking

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]
_TIMEOUT = 30


class GoogleSheetsService:

    def __init__(self) -> None:
        self._enabled = False
        self._client: gspread.Client | None = None
        self._sheet_id = career_week_settings.google_sheets_id

        raw = career_week_settings.google_service_account_json
        if not raw:
            logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON не задан — Google Sheets отключён")
            return

        try:
            sa_info = json.loads(raw)
            creds = Credentials.from_service_account_info(sa_info, scopes=_SCOPES)
            self._client = gspread.authorize(creds)  # type: ignore[attr-defined]
            self._enabled = True
            logger.info("GoogleSheetsService инициализирован (sheet_id=%s)", self._sheet_id)
        except Exception:
            logger.exception("Ошибка инициализации GoogleSheetsService")

    # ── Внутренние ────────────────────────────────────────────────────────────

    def _get_sheet_sync(self, sheet_name: str) -> gspread.Worksheet:
        assert self._client is not None
        spreadsheet = self._client.open_by_key(self._sheet_id)
        return spreadsheet.worksheet(sheet_name)

    async def _get_sheet(self, sheet_name: str) -> gspread.Worksheet:
        return await asyncio.wait_for(
            asyncio.to_thread(self._get_sheet_sync, sheet_name),
            timeout=_TIMEOUT,
        )

    # ── Чтение ────────────────────────────────────────────────────────────────

    async def get_partners(self) -> list[dict]:
        if not self._enabled:
            return []
        try:
            ws = await self._get_sheet("partners")
            rows: list[dict] = await asyncio.wait_for(
                asyncio.to_thread(ws.get_all_records),
                timeout=_TIMEOUT,
            )
            return [r for r in rows if r.get("name")]
        except Exception:
            logger.exception("Ошибка чтения листа partners")
            raise

    async def get_schedule(self) -> list[dict]:
        if not self._enabled:
            return []
        try:
            ws = await self._get_sheet("schedule")
            rows: list[dict] = await asyncio.wait_for(
                asyncio.to_thread(ws.get_all_records),
                timeout=_TIMEOUT,
            )
            return rows
        except Exception:
            logger.exception("Ошибка чтения листа schedule")
            raise

    async def get_roast_slots(self) -> list[dict]:
        if not self._enabled:
            return []
        try:
            ws = await self._get_sheet("roast_slots")
            rows: list[dict] = await asyncio.wait_for(
                asyncio.to_thread(ws.get_all_records),
                timeout=_TIMEOUT,
            )
            return rows
        except Exception:
            logger.exception("Ошибка чтения листа roast_slots")
            raise

    async def get_programs(self) -> list[dict]:
        """
        Читает лист "programs".
        Ожидаемые колонки: name, level (бакалавриат / магистратура).
        Возвращает list[dict] с ключами name, level.
        """
        if not self._enabled:
            return []
        try:
            ws = await self._get_sheet("programs")
            rows: list[dict] = await asyncio.wait_for(
                asyncio.to_thread(ws.get_all_records),
                timeout=_TIMEOUT,
            )
            return [
                {"name": str(r["name"]), "level": str(r.get("level", "")).strip().lower()}
                for r in rows
                if r.get("name")
            ]
        except Exception:
            logger.exception("Ошибка чтения листа programs")
            raise

    async def get_skills(self) -> list[str]:
        """
        Читает лист "skills", колонку "name".
        Возвращает список строк.
        """
        if not self._enabled:
            return []
        try:
            ws = await self._get_sheet("skills")
            rows: list[dict] = await asyncio.wait_for(
                asyncio.to_thread(ws.get_all_records),
                timeout=_TIMEOUT,
            )
            return [str(r["name"]) for r in rows if r.get("name")]
        except Exception:
            logger.exception("Ошибка чтения листа skills")
            raise

    async def get_admins(self) -> list[int]:
        if not self._enabled:
            return []
        try:
            ws = await self._get_sheet("admins")
            rows: list[dict] = await asyncio.wait_for(
                asyncio.to_thread(ws.get_all_records),
                timeout=_TIMEOUT,
            )
            result = []
            for r in rows:
                try:
                    result.append(int(r["telegram_id"]))
                except (KeyError, ValueError, TypeError):
                    pass
            return result
        except Exception:
            logger.exception("Ошибка чтения листа admins")
            raise

    # ── Запись ────────────────────────────────────────────────────────────────

    async def append_registration(
        self,
        reg: CareerWeekRegistration,
        user_name: str,
    ) -> None:
        if not self._enabled:
            logger.warning("append_registration: Sheets отключён, запись пропущена (code=%s)", reg.code)
            return
        logger.info(
            "append_registration: попытка записи — user_id=%s code=%s direction=%s",
            reg.user_id, reg.code, reg.direction,
        )
        try:
            ws = await self._get_sheet("registrations")
            row = [
                str(reg.user_id),
                user_name,
                reg.code,
                reg.direction,
                reg.program,
                reg.course,
                ", ".join(reg.skills),
                reg.registered_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
            await asyncio.wait_for(
                asyncio.to_thread(ws.append_row, row),
                timeout=_TIMEOUT,
            )
            logger.info("append_registration: успешно записано (code=%s)", reg.code)
        except Exception as e:
            logger.error("append_registration: ошибка записи (code=%s): %s", reg.code, e)
            raise

    async def append_roast_booking(
        self,
        booking: RoastBooking,
        user_code: str,
        full_name: str | None = None,
    ) -> None:
        if not self._enabled:
            return
        try:
            ws = await self._get_sheet("roast_registrations")
            if booking.resume_file_id:
                resume_type = "telegram_file"
                resume_value = booking.resume_file_id
            elif booking.resume_url:
                resume_type = "url"
                resume_value = booking.resume_url
            else:
                resume_type = "none"
                resume_value = "не загружено"
            booked_at_str = (
                booking.booked_at.strftime("%Y-%m-%d %H:%M:%S")
                if booking.booked_at
                else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )
            cancelled_at_str = (
                booking.cancelled_at.strftime("%Y-%m-%d %H:%M:%S")
                if booking.cancelled_at
                else ""
            )
            # Колонки: booking_id | user_code | full_name | slot_id | type |
            #          direction | resume_type | resume_value | booked_at | cancelled_at
            row = [
                str(booking.id),
                user_code,
                full_name or "",
                booking.slot_id,
                booking.slot_type,
                booking.direction,
                resume_type,
                resume_value,
                booked_at_str,
                cancelled_at_str,
            ]
            await asyncio.wait_for(
                asyncio.to_thread(ws.append_row, row),
                timeout=_TIMEOUT,
            )
        except Exception:
            logger.exception("Ошибка записи записи на прожарку в Sheets")
            raise

    async def update_roast_cancellation(self, booking_id: str) -> None:
        if not self._enabled:
            return
        try:
            ws = await self._get_sheet("roast_registrations")
            cancelled_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            def _find_and_update() -> None:
                col_values = ws.col_values(1)  # booking_id в первой колонке
                for idx, val in enumerate(col_values):
                    if val == booking_id:
                        row_num = idx + 1
                        # Колонка 10 = cancelled_at (после добавления full_name)
                        ws.update_cell(row_num, 10, cancelled_str)
                        return

            await asyncio.wait_for(
                asyncio.to_thread(_find_and_update),
                timeout=_TIMEOUT,
            )
        except Exception:
            logger.exception("Ошибка обновления отмены прожарки в Sheets")
            raise

    async def append_waitlist(
        self,
        user_id: str,
        telegram_id: int,
        username: str,
        first_name: str,
    ) -> None:
        if not self._enabled:
            return
        try:
            ws = await self._get_sheet("waitlist")
            row = [
                user_id,
                str(telegram_id),
                username,
                first_name,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ]
            await asyncio.wait_for(
                asyncio.to_thread(ws.append_row, row),
                timeout=_TIMEOUT,
            )
        except Exception:
            logger.exception("Ошибка записи в лист waitlist")
            raise

    async def update_admins(self, telegram_ids: list[int]) -> None:
        if not self._enabled:
            return
        try:
            ws = await self._get_sheet("admins")

            def _rewrite() -> None:
                ws.clear()
                ws.append_row(["telegram_id"])
                for tid in telegram_ids:
                    ws.append_row([tid])

            await asyncio.wait_for(
                asyncio.to_thread(_rewrite),
                timeout=_TIMEOUT,
            )
        except Exception:
            logger.exception("Ошибка обновления листа admins")
            raise
