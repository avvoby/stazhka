from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.entities.application import Application
from src.domain.value_objects.application_stage import ApplicationStage
from src.infrastructure.database.models import ApplicationModel, UserModel, VacancyModel


class ApplicationRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Mappers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(
        model: ApplicationModel,
        vacancy: VacancyModel | None = None,
    ) -> Application:
        return Application(
            id=model.id,
            user_id=model.user_id,
            vacancy_id=model.vacancy_id,
            stage=ApplicationStage(model.stage),
            notes=model.notes,
            applied_at=model.applied_at,
            next_step=model.next_step,
            next_step_date=model.next_step_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
            vacancy_title=vacancy.title if vacancy else "",
            vacancy_company=vacancy.company if vacancy else "",
            vacancy_url=vacancy.source_url if vacancy else "",
        )

    @staticmethod
    def _to_model(application: Application) -> ApplicationModel:
        return ApplicationModel(
            id=application.id,
            user_id=application.user_id,
            vacancy_id=application.vacancy_id,
            stage=str(application.stage),
            notes=application.notes,
            applied_at=application.applied_at,
            next_step=application.next_step,
            next_step_date=application.next_step_date,
            created_at=application.created_at,
            updated_at=application.updated_at,
        )

    # ── Queries ──────────────────────────────────────────────────────────────

    async def get_by_id(self, application_id: UUID) -> Application | None:
        result = await self._session.execute(
            select(ApplicationModel).where(ApplicationModel.id == application_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_user(
        self,
        user_id: UUID,
        stage: ApplicationStage | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Application]:
        stmt = (
            select(ApplicationModel)
            .options(joinedload(ApplicationModel.vacancy))
            .where(ApplicationModel.user_id == user_id)
        )
        if stage:
            stmt = stmt.where(ApplicationModel.stage == str(stage))

        stmt = stmt.order_by(ApplicationModel.updated_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        # unique() нужен при joinedload чтобы убрать дубли из JOIN
        models = result.scalars().unique().all()
        return [self._to_domain(m, m.vacancy) for m in models]

    async def get_by_user_and_vacancy(
        self, user_id: UUID, vacancy_id: UUID
    ) -> Application | None:
        result = await self._session.execute(
            select(ApplicationModel).where(
                ApplicationModel.user_id == user_id,
                ApplicationModel.vacancy_id == vacancy_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, application: Application) -> Application:
        model = self._to_model(application)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, application: Application) -> Application:
        result = await self._session.execute(
            select(ApplicationModel).where(ApplicationModel.id == application.id)
        )
        model = result.scalar_one()
        model.stage = str(application.stage)
        model.notes = application.notes
        model.applied_at = application.applied_at
        model.next_step = application.next_step
        model.next_step_date = application.next_step_date
        model.updated_at = application.updated_at
        await self._session.flush()
        return self._to_domain(model)

    async def delete(self, application_id: UUID) -> None:
        result = await self._session.execute(
            select(ApplicationModel).where(ApplicationModel.id == application_id)
        )
        model = result.scalar_one()
        await self._session.delete(model)
        await self._session.flush()

    async def count_by_user(self, user_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).where(ApplicationModel.user_id == user_id)
        )
        return result.scalar_one()

    async def get_stale_applied(self, days: int = 7) -> list[tuple[int, Application]]:
        """
        Возвращает (telegram_id, application) для заявок в статусе applied,
        которые не обновлялись более `days` дней.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(ApplicationModel, UserModel.telegram_id)
            .join(UserModel, ApplicationModel.user_id == UserModel.id)
            .options(joinedload(ApplicationModel.vacancy))
            .where(
                ApplicationModel.stage == str(ApplicationStage.APPLIED),
                ApplicationModel.updated_at < cutoff,
            )
        )
        result = await self._session.execute(stmt)
        rows = result.unique().all()
        return [
            (int(telegram_id), self._to_domain(app, app.vacancy))
            for app, telegram_id in rows
        ]

    async def get_interview_tomorrow(self) -> list[tuple[int, Application]]:
        """
        Возвращает (telegram_id, application) для заявок в статусе interview
        где next_step_date = завтра.
        """
        tomorrow_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        stmt = (
            select(ApplicationModel, UserModel.telegram_id)
            .join(UserModel, ApplicationModel.user_id == UserModel.id)
            .options(joinedload(ApplicationModel.vacancy))
            .where(
                ApplicationModel.stage == str(ApplicationStage.INTERVIEW),
                ApplicationModel.next_step_date >= tomorrow_start,
                ApplicationModel.next_step_date < tomorrow_end,
            )
        )
        result = await self._session.execute(stmt)
        rows = result.unique().all()
        return [
            (int(telegram_id), self._to_domain(app, app.vacancy))
            for app, telegram_id in rows
        ]
