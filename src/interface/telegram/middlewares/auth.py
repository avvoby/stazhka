from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from src.application.use_cases.onboarding import GetOrCreateUser
from src.interface.telegram.middlewares.container import Container
from src.interface.telegram.states.forms import OnboardingStates


# Колбэки, которые пропускаем без проверки профиля
_ONBOARDING_CALLBACKS = {
    "privacy:accept", "skills:done",
    "onboard_accept",
    "career_week_start", "waitlist_menu", "waitlist_join", "waitlist_back_main",
}
_ONBOARDING_PREFIXES = ("spec:", "course:", "skill:", "edit:", "cw:")


class AuthMiddleware(BaseMiddleware):
    """
    Определяет пользователя по telegram_id и кладёт в data["user"].
    Если пользователь не прошёл онбординг и это не /start — блокирует.

    Регистрируется на dp.update, поэтому event всегда Update.
    Реальный message/callback_query извлекается из update.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # dp.update передаёт Update, извлекаем вложенный объект
        message, callback = self._extract_inner(event)
        telegram_user = (
            message.from_user if message else
            callback.from_user if callback else
            None
        )

        if telegram_user is None:
            return await handler(event, data)

        container: Container = data["container"]
        use_case = GetOrCreateUser(container.user_repo)

        user = await use_case.execute(
            telegram_id=telegram_user.id,
            first_name=telegram_user.first_name or "",
            last_name=telegram_user.last_name or "",
            username=telegram_user.username or "",
            language_code=telegram_user.language_code or "ru",
        )
        data["user"] = user

        # Пропускаем /start без проверки профиля
        if message and message.text and message.text.startswith("/start"):
            return await handler(event, data)

        # Пропускаем career_week и waitlist колбэки без проверки профиля
        cb_data = callback.data if callback else None
        if cb_data and (
            cb_data.startswith("cw:") or
            cb_data.startswith("cw_") or
            cb_data in {
                "career_week_start",
                "waitlist_menu", "waitlist_join", "waitlist_back_main",
                "onboard_accept",
            }
        ):
            return await handler(event, data)

        # Пропускаем стандартные колбэки онбординга
        if callback and callback.data and self._is_onboarding_callback(callback.data):
            return await handler(event, data)

        # Пропускаем если пользователь уже внутри FSM-флоу онбординга
        fsm: FSMContext | None = data.get("state")
        if fsm is not None:
            current = await fsm.get_state()
            if current is not None and current.startswith("OnboardingStates:"):
                return await handler(event, data)

        # Онбординг не пройден — у пользователя нет профиля с контекстом
        if not user.profile or not user.profile.about:
            if message:
                await message.answer("Сначала напиши /start, чтобы пройти регистрацию.")
            elif callback:
                await callback.answer(
                    "Сначала напиши /start, чтобы пройти регистрацию.",
                    show_alert=True,
                )
            return None

        return await handler(event, data)

    @staticmethod
    def _is_onboarding_callback(data: str) -> bool:
        if data in _ONBOARDING_CALLBACKS:
            return True
        return any(data.startswith(p) for p in _ONBOARDING_PREFIXES)

    @staticmethod
    def _extract_inner(
        event: TelegramObject,
    ) -> tuple[Message | None, CallbackQuery | None]:
        """Извлекает message и callback_query из Update."""
        if isinstance(event, Update):
            return event.message, event.callback_query
        # На случай если middleware зарегистрирован на router уровне
        if isinstance(event, Message):
            return event, None
        if isinstance(event, CallbackQuery):
            return None, event
        return None, None
