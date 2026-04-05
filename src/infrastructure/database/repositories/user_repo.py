from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.entities.user import User, UserProfile
from src.domain.value_objects.search_status import SearchStatus
from src.infrastructure.database.models import UserModel, UserProfileModel


class UserRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Mappers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _profile_to_domain(model: UserProfileModel) -> UserProfile:
        return UserProfile(
            id=model.id,
            user_id=model.user_id,
            full_name=model.full_name,
            university=model.university,
            specialty=model.specialty,
            graduation_year=model.graduation_year,
            skills=list(model.skills or []),
            desired_position=model.desired_position,
            desired_city=model.desired_city,
            resume_url=model.resume_url,
            about=model.about,
            search_status=SearchStatus(model.search_status),
            gpa=model.gpa,
            language=model.language,
            experience=model.experience,
            expected_salary=model.expected_salary,
            notifications_enabled=model.notifications_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _profile_to_model(profile: UserProfile) -> UserProfileModel:
        return UserProfileModel(
            id=profile.id,
            user_id=profile.user_id,
            full_name=profile.full_name,
            university=profile.university,
            specialty=profile.specialty,
            graduation_year=profile.graduation_year,
            skills=profile.skills,
            desired_position=profile.desired_position,
            desired_city=profile.desired_city,
            resume_url=profile.resume_url,
            about=profile.about,
            search_status=str(profile.search_status),
            gpa=profile.gpa,
            language=profile.language,
            experience=profile.experience,
            expected_salary=profile.expected_salary,
            notifications_enabled=profile.notifications_enabled,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        profile = (
            UserRepositoryImpl._profile_to_domain(model.profile)
            if model.profile
            else None
        )
        return User(
            id=model.id,
            telegram_id=model.telegram_id,
            username=model.username,
            first_name=model.first_name,
            last_name=model.last_name,
            language_code=model.language_code,
            is_active=model.is_active,
            is_blocked=model.is_blocked,
            created_at=model.created_at,
            updated_at=model.updated_at,
            profile=profile,
        )

    @staticmethod
    def _to_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_active=user.is_active,
            is_blocked=user.is_blocked,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    # ── Queries ──────────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel)
            .options(joinedload(UserModel.profile))
            .where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(
            select(UserModel)
            .options(joinedload(UserModel.profile))
            .where(UserModel.telegram_id == telegram_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, user: User) -> User:
        model = self._to_model(user)
        self._session.add(model)
        await self._session.flush()
        # Перезапрашиваем с joinedload чтобы избежать lazy load в async контексте
        result = await self._session.execute(
            select(UserModel)
            .options(joinedload(UserModel.profile))
            .where(UserModel.id == model.id)
        )
        return self._to_domain(result.scalar_one())

    async def update(self, user: User) -> User:
        result = await self._session.execute(
            select(UserModel)
            .options(joinedload(UserModel.profile))
            .where(UserModel.id == user.id)
        )
        model = result.scalar_one()
        model.username = user.username
        model.first_name = user.first_name
        model.last_name = user.last_name
        model.language_code = user.language_code
        model.is_active = user.is_active
        model.is_blocked = user.is_blocked
        model.updated_at = user.updated_at
        await self._session.flush()
        return self._to_domain(model)

    async def get_profile(self, user_id: UUID) -> UserProfile | None:
        result = await self._session.execute(
            select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._profile_to_domain(model) if model else None

    async def upsert_profile(self, profile: UserProfile) -> UserProfile:
        result = await self._session.execute(
            select(UserProfileModel).where(
                UserProfileModel.user_id == profile.user_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.full_name = profile.full_name
            existing.university = profile.university
            existing.specialty = profile.specialty
            existing.graduation_year = profile.graduation_year
            existing.skills = profile.skills
            existing.desired_position = profile.desired_position
            existing.desired_city = profile.desired_city
            existing.resume_url = profile.resume_url
            existing.about = profile.about
            existing.search_status = str(profile.search_status)
            existing.gpa = profile.gpa
            existing.language = profile.language
            existing.experience = profile.experience
            existing.expected_salary = profile.expected_salary
            existing.notifications_enabled = profile.notifications_enabled
            existing.updated_at = profile.updated_at
            await self._session.flush()
            return self._profile_to_domain(existing)

        model = self._profile_to_model(profile)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._profile_to_domain(model)

    async def get_all_notifiable(self) -> list[tuple[int, "UserProfile"]]:
        """
        Возвращает (telegram_id, profile) для пользователей с
        notifications_enabled=True и заполненной специализацией.
        """
        result = await self._session.execute(
            select(UserProfileModel, UserModel.telegram_id)
            .join(UserModel, UserProfileModel.user_id == UserModel.id)
            .where(
                UserProfileModel.notifications_enabled.is_(True),
                UserProfileModel.specialty != "",
            )
        )
        rows = result.all()
        return [
            (int(telegram_id), self._profile_to_domain(profile))
            for profile, telegram_id in rows
        ]
