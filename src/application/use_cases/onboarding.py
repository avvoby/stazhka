import asyncio
from datetime import datetime

from src.domain.entities.user import User, UserProfile
from src.domain.repositories.user_repo import UserRepository
from src.domain.value_objects.search_status import SearchStatus


class GetOrCreateUser:
    """Возвращает существующего пользователя или создаёт нового."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(
        self,
        telegram_id: int,
        first_name: str = "",
        last_name: str = "",
        username: str = "",
        language_code: str = "ru",
    ) -> User:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user:
            # Обновляем мета-данные если изменились
            changed = (
                user.first_name != first_name
                or user.last_name != last_name
                or user.username != username
            )
            if changed:
                user.first_name = first_name
                user.last_name = last_name
                user.username = username
                user.updated_at = datetime.utcnow()
                user = await self._user_repo.update(user)
            return user

        new_user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language_code=language_code,
        )
        return await self._user_repo.create(new_user)


class SaveUserContext:
    """Сохраняет контекст пользователя и запускает AI-парсинг в фоне."""

    def __init__(self, user_repo: UserRepository, ai_service: object) -> None:
        self._user_repo = user_repo
        self._ai_service = ai_service

    async def execute(
        self,
        user_id: object,
        raw_text: str,
        search_status: SearchStatus = SearchStatus.ACTIVE,
    ) -> UserProfile:
        # Получаем или создаём профиль с raw_text
        profile = await self._user_repo.get_profile(user_id)  # type: ignore[arg-type]
        if profile is None:
            profile = UserProfile(
                user_id=user_id,  # type: ignore[arg-type]
            )

        profile.about = raw_text
        profile.search_status = search_status
        profile.updated_at = datetime.utcnow()
        saved_profile = await self._user_repo.upsert_profile(profile)

        # AI-парсинг запускается в фоне, не блокирует ответ пользователю
        asyncio.create_task(
            self._parse_profile_with_ai(saved_profile)
        )

        return saved_profile

    async def _parse_profile_with_ai(self, profile: UserProfile) -> None:
        """Фоновая задача: парсит текст профиля через AI и обновляет поля."""
        try:
            parsed = await self._ai_service.parse_user_context(profile.about)  # type: ignore[attr-defined]
            if parsed.get("full_name"):
                profile.full_name = parsed["full_name"]
            if parsed.get("university"):
                profile.university = parsed["university"]
            if parsed.get("specialty"):
                profile.specialty = parsed["specialty"]
            if parsed.get("graduation_year"):
                profile.graduation_year = parsed["graduation_year"]
            if parsed.get("skills"):
                profile.skills = parsed["skills"]
            if parsed.get("desired_position"):
                profile.desired_position = parsed["desired_position"]
            if parsed.get("desired_city"):
                profile.desired_city = parsed["desired_city"]
            profile.updated_at = datetime.utcnow()
            await self._user_repo.upsert_profile(profile)
        except Exception:
            pass  # Фоновая задача — не критично
