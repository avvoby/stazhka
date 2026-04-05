from datetime import datetime
from uuid import UUID

from src.domain.entities.application import Application
from src.domain.repositories.application_repo import ApplicationRepository
from src.domain.value_objects.application_stage import ApplicationStage


class GetUserApplications:
    """Возвращает список откликов пользователя с опциональной фильтрацией по этапу."""

    def __init__(self, application_repo: ApplicationRepository) -> None:
        self._application_repo = application_repo

    async def execute(
        self,
        user_id: UUID,
        stage: ApplicationStage | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Application]:
        return await self._application_repo.get_by_user(
            user_id=user_id,
            stage=stage,
            limit=limit,
            offset=offset,
        )


class UpdateApplicationStage:
    """Переводит отклик на новый этап воронки."""

    def __init__(self, application_repo: ApplicationRepository) -> None:
        self._application_repo = application_repo

    async def execute(
        self,
        application_id: UUID,
        new_stage: ApplicationStage,
        notes: str = "",
        next_step: str = "",
        next_step_date: datetime | None = None,
    ) -> Application:
        application = await self._application_repo.get_by_id(application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")

        application.advance_to(new_stage)

        if notes:
            application.notes = notes
        if next_step:
            application.next_step = next_step
        if next_step_date:
            application.next_step_date = next_step_date

        return await self._application_repo.update(application)
