import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.config import settings
from src.events.career_week.config import career_week_settings
from src.infrastructure.external.hh_client import HHClient
from src.infrastructure.scheduler.tasks import (
    check_application_followups,
    check_interview_reminders,
    send_daily_digest,
)
from src.interface.telegram.handlers import ai_features, applications, onboarding, vacancies
from src.interface.telegram.middlewares.auth import AuthMiddleware
from src.interface.telegram.middlewares.container import ContainerMiddleware

logger = structlog.get_logger()


def build_dispatcher(
    storage: RedisStorage,
    cw_sheets: GoogleSheetsService | None = None,
    cw_cache: CareerWeekCacheService | None = None,
    cw_registration: CareerWeekRegistrationService | None = None,
) -> Dispatcher:
    dp = Dispatcher(storage=storage)

    # Middleware — порядок важен: сначала container, потом auth
    dp.update.middleware(ContainerMiddleware(
        cw_sheets=cw_sheets,
        cw_cache=cw_cache,
        cw_registration=cw_registration,
    ))
    dp.update.middleware(AuthMiddleware())

    # Роутеры
    dp.include_router(onboarding.router)
    dp.include_router(vacancies.router)
    dp.include_router(applications.router)
    dp.include_router(ai_features.router)

    # Career Week (условно)
    if career_week_settings.career_week_enabled:
        from src.events.career_week.handlers import admin as cw_admin
        from src.events.career_week.handlers import main as cw_main
        from src.events.career_week.handlers import partners as cw_partners
        from src.events.career_week.handlers import roasts as cw_roasts
        from src.events.career_week.handlers import schedule as cw_schedule
        dp.include_router(cw_main.router)
        dp.include_router(cw_partners.router)
        dp.include_router(cw_schedule.router)
        dp.include_router(cw_roasts.router)
        dp.include_router(cw_admin.router)

    return dp


def build_scheduler(bot: Bot, hh_client: HHClient) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    # Ежедневно в 09:00 — напоминание перед интервью
    scheduler.add_job(
        check_interview_reminders,
        trigger="cron",
        hour=9,
        minute=0,
        kwargs={"bot": bot},
        id="interview_reminders",
        replace_existing=True,
    )

    # Ежедневно в 10:00 — followup по подвисшим заявкам
    scheduler.add_job(
        check_application_followups,
        trigger="cron",
        hour=10,
        minute=0,
        kwargs={"bot": bot},
        id="application_followups",
        replace_existing=True,
    )

    # Ежедневно в 10:00 — дайджест новых вакансий
    scheduler.add_job(
        send_daily_digest,
        trigger="cron",
        hour=10,
        minute=0,
        kwargs={"bot": bot, "hh_client": hh_client},
        id="daily_digest",
        replace_existing=True,
    )

    return scheduler


async def main() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ]
    )

    storage = RedisStorage.from_url(settings.redis.url)

    bot = Bot(
        token=settings.telegram.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    hh_client = HHClient()

    # Career Week сервисы (только если включено)
    cw_sheets = None
    cw_cache = None
    cw_registration = None
    if career_week_settings.career_week_enabled:
        from redis.asyncio import from_url as redis_from_url

        from src.events.career_week.services.cache import CareerWeekCacheService
        from src.events.career_week.services.registration import CareerWeekRegistrationService
        from src.events.career_week.services.sheets import GoogleSheetsService

        redis_client = redis_from_url(settings.redis.url, decode_responses=True)
        cw_sheets = GoogleSheetsService()
        cw_cache = CareerWeekCacheService(redis_client)
        cw_registration = CareerWeekRegistrationService()

        # Первоначальная синхронизация кэша из Sheets (если Sheets включён)
        if cw_sheets._enabled:
            try:
                stats = await cw_cache.sync_from_sheets(cw_sheets)
                await logger.ainfo("CareerWeek кэш загружен", **stats)
            except Exception:
                await logger.awarning("CareerWeek: не удалось синхронизировать кэш при старте")

    dp = build_dispatcher(storage, cw_sheets=cw_sheets, cw_cache=cw_cache, cw_registration=cw_registration)
    scheduler = build_scheduler(bot, hh_client)

    await logger.ainfo("Стажка bot started", env=settings.app.env)

    scheduler.start()
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
    finally:
        scheduler.shutdown(wait=False)
        await hh_client.close()
        await logger.ainfo("Стажка bot stopped")
        await bot.session.close()
        await storage.close()


if __name__ == "__main__":
    asyncio.run(main())
