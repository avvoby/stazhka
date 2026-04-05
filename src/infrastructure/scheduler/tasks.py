"""
Scheduled tasks (APScheduler 3.x):

  check_application_followups  — ежедневно в 10:00
  check_interview_reminders    — ежедневно в 09:00
  send_daily_digest            — ежедневно в 10:00
"""
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from src.infrastructure.database.connection import AsyncSessionFactory
from src.infrastructure.database.repositories.application_repo import ApplicationRepositoryImpl
from src.infrastructure.database.repositories.user_repo import UserRepositoryImpl
from src.infrastructure.external.hh_client import HHClient, SPEC_TO_QUERY, TECH_SKILLS_FOR_QUERY
from src.interface.telegram.keyboards.main import (
    digest_keyboard,
    followup_keyboard,
    interview_reminder_keyboard,
)

logger = logging.getLogger(__name__)


async def _safe_send(bot: Bot, chat_id: int, text: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
    """Отправляет сообщение, молча игнорирует заблокированных пользователей."""
    try:
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logger.debug("Cannot send to %d: %s", chat_id, e)
    except Exception as e:
        logger.warning("Unexpected error sending to %d: %s", chat_id, e)


async def check_application_followups(bot: Bot) -> None:
    """
    Ищет заявки в статусе «Подано», которые не обновлялись 7+ дней,
    и напоминает пользователю уточнить статус.
    """
    logger.info("Scheduler: check_application_followups")
    async with AsyncSessionFactory() as session:
        repo = ApplicationRepositoryImpl(session)
        rows = await repo.get_stale_applied(days=7)

    logger.info("Followup: найдено %d устаревших заявок", len(rows))

    for telegram_id, app in rows:
        company = app.vacancy_company or app.vacancy_title or "компанию"
        text = (
            f"👋 Как дела с <b>{company}</b>?\n\n"
            f"Прошло 7 дней с подачи заявки. Получил ответ?"
        )
        await _safe_send(
            bot,
            telegram_id,
            text,
            parse_mode="HTML",
            reply_markup=followup_keyboard(str(app.id)),
        )


async def check_interview_reminders(bot: Bot) -> None:
    """
    Ищет интервью на завтра и отправляет напоминание с предложением подготовиться.
    """
    logger.info("Scheduler: check_interview_reminders")
    async with AsyncSessionFactory() as session:
        repo = ApplicationRepositoryImpl(session)
        rows = await repo.get_interview_tomorrow()

    logger.info("Reminders: найдено %d интервью завтра", len(rows))

    for telegram_id, app in rows:
        company = app.vacancy_company or "компании"
        text = (
            f"⏰ Завтра интервью в <b>{company}</b>!\n\n"
            f"Готов? Могу помочь подготовиться."
        )
        await _safe_send(
            bot,
            telegram_id,
            text,
            parse_mode="HTML",
            reply_markup=interview_reminder_keyboard(str(app.id)),
        )


async def send_daily_digest(bot: Bot, hh_client: HHClient) -> None:
    """
    Находит пользователей с включёнными уведомлениями,
    подбирает 3 вакансии под профиль и отправляет дайджест.
    """
    logger.info("Scheduler: send_daily_digest")
    async with AsyncSessionFactory() as session:
        user_repo = UserRepositoryImpl(session)
        notifiable = await user_repo.get_all_notifiable()

    logger.info("Digest: найдено %d пользователей", len(notifiable))

    for telegram_id, profile in notifiable:
        try:
            # Строим поисковый запрос из профиля
            spec = profile.specialty or ""
            base = SPEC_TO_QUERY.get(spec, spec or "стажировка")
            if profile.skills:
                tech = [s for s in profile.skills if s in TECH_SKILLS_FOR_QUERY]
                if tech:
                    base += " " + " ".join(tech[:2])

            raw_list = await hh_client.search_vacancies(
                base,
                {"experience": "noExperience", "per_page": 10, "area": 1},
            )
            if not raw_list:
                continue

            top3 = raw_list[:3]
            lines = []
            for i, v in enumerate(top3, 1):
                employer = (v.get("employer") or {}).get("name", "")
                name = v.get("name", "")
                lines.append(f"{i}. <b>{name}</b> — {employer}")

            first_name = ""
            # Получаем имя из users таблицы — берём telegram_id как идентификатор
            # Достаточно имени из первого сообщения; используем просто "привет"
            text = (
                f"🌅 <b>Доброе утро!</b>\n\n"
                f"Нашёл 3 новые стажировки для тебя:\n\n"
                + "\n".join(lines)
                + "\n\n"
            )
            await _safe_send(
                bot,
                telegram_id,
                text,
                parse_mode="HTML",
                reply_markup=digest_keyboard(),
            )
        except Exception as e:
            logger.warning("Digest failed for user %d: %s", telegram_id, e)
